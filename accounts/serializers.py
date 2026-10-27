from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.core.mail import send_mail
from django.conf import settings
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


from .models import Restaurant, User

User = get_user_model()


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = "email"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ensure the field label/representation explicitly matches 'email'
        if "email" not in self.fields and "username" in self.fields:
            self.fields["email"] = self.fields.pop("username")

    def validate(self, attrs):
        # Fallback to map email to username key if needed by authenticate backend
        email = attrs.get("email") or attrs.get("username")
        if email:
            attrs[self.username_field] = email
        return super().validate(attrs)

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["restaurant_id"] = getattr(user, "restaurant_id", None)
        token["role"] = getattr(user, "role", None)
        token["user_id"] = user.pk
        return token


class UserMeSerializer(serializers.ModelSerializer):
    restaurant_name = serializers.CharField(
        source="restaurant.name", read_only=True, default=None
    )

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "display_name",
            "role",
            "restaurant_id",
            "restaurant_name",
            "phone",
            "avatar",
            "must_change_password",
            "is_active",
            "date_joined",
            "last_login",
        ]
        read_only_fields = ["id", "email", "role", "restaurant"]

    def update(self, instance, validated_data):
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        
        if 'avatar' in validated_data:
            instance.avatar = validated_data['avatar']

        instance.save()
        return instance


class RestaurantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Restaurant
        fields = [
            "id",
            "name",
            "address",
            "contact_number",
            "tin",
            "is_vat_registered",
            "receipt_footer",
            "timezone",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class RegisterSerializer(serializers.Serializer):
    restaurant_name = serializers.CharField(max_length=150, required=True)
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True)
    first_name = serializers.CharField(max_length=150, required=False, allow_blank=True, default="")
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True, default="")
    phone = serializers.CharField(max_length=30, required=False, allow_blank=True, default="")

    def validate_email(self, value):
        normalized_email = value.lower().strip()
        if User.objects.filter(email=normalized_email).exists():
            raise serializers.ValidationError("A user with this email address already exists.")
        return normalized_email

    def validate_password(self, value):
        validate_password(value)
        return value

    def create(self, validated_data):
        restaurant = Restaurant.objects.create(name=validated_data["restaurant_name"])
        
        # UserManager.create_user automatically sets username=email
        user = User.objects.create_user(
            email=validated_data["email"],
            password=validated_data["password"],
            first_name=validated_data.get("first_name", ""),
            last_name=validated_data.get("last_name", ""),
            phone=validated_data.get("phone", ""),
            restaurant=restaurant,
            role=User.Role.OWNER,
        )
        return user


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True)

    def validate_new_password(self, value):
        validate_password(value)
        return value


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)


class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField(required=True)
    token = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, write_only=True)

    def validate_new_password(self, value):
        validate_password(value)
        return value


class RequestEmailChangeSerializer(serializers.Serializer):
    new_email = serializers.EmailField(required=True)

    def validate_new_email(self, value):
        normalized_email = value.lower().strip()
        if User.objects.filter(email=normalized_email).exists():
            raise serializers.ValidationError("This email address is already taken.")
        return normalized_email

class StaffSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "display_name",
            "role",
            "phone",
            "avatar",
            "is_active",
            "date_joined",
        ]
        read_only_fields = ["id", "display_name", "date_joined"]

    def validate_email(self, value):
        normalized_email = value.lower().strip()
        queryset = User.objects.filter(email=normalized_email)
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError("A user with this email address already exists.")
        return normalized_email

    def create(self, validated_data):
        email = validated_data.pop("email")
        restaurant = validated_data.get("restaurant")
        
        # Create user with an unusable initial password until they set their own
        user = User.objects.create_user(
            email=email,
            password=None, 
            must_change_password=True,
            is_active=True,
            **validated_data
        )
        user.set_unusable_password()
        user.save(update_fields=["password"])

        # Generate secure token for setting the password
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        
        frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
        setup_link = f"{frontend_url}/set-password/{uid}/{token}/"

        # Send secure invitation email
        send_mail(
            subject="You're invited to join TAPSI",
            message=f"Hello {user.first_name},\n\nYou have been added as staff for {restaurant.name if restaurant else 'your restaurant'}.\n\nPlease click the link below to set your password and activate your account:\n\n{setup_link}\n\nThis link will expire shortly.",
            from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "webmaster@localhost"),
            recipient_list=[user.email],
            fail_silently=False,
        )

        return user