export interface RecipeLine {
  id: number;
  ingredient: {
    id: number;
    name: string;
    unit_of_measure: string;
    average_unit_cost: string;
  };
  quantity: string;
  line_cost: string;
}

export interface RecipeDetailData {
  id: number;
  name: string;
  menu_item?: { id: number; name: string; price: string } | null;
  addon?: { id: number; name: string; price: string } | null;
  cost: string;
  margin?: number | null;
  lines: RecipeLine[];
}

export interface IngredientOption {
  id: number;
  name: string;
  unit_of_measure: string;
}

export interface RecipeFormMeta {
  ingredients: IngredientOption[];
}

export interface MenuItemOption {
  id: number;
  name: string;
}

export interface AddonOption {
  id: number;
  name: string;
}

export interface RecipeFormMetaOptions {
  menu_items: MenuItemOption[];
  addons: AddonOption[];
  ingredients: IngredientOption[];
}

export interface RecipeFormData {
  name: string;
  menu_item_id?: number | string | null;
  addon_id?: number | string | null;
  ingredient_id?: number | string | null;
  quantity?: number | string | null;
}

export interface RecipeListItem {
  id: number;
  name: string;
  menu_item?: { id: number; name: string } | null;
  addon?: { id: number; name: string } | null;
  cost: string;
  margin?: number | null;
}

export interface RecipeListResponse {
  recipes: RecipeListItem[];
}