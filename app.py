import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import os
from weasyprint import HTML
from datetime import datetime

class NutritionPlanCreator:
    def __init__(self, root):
        self.root = root
        self.root.title("Nutrition Plan Creator")
        self.root.geometry("1200x800")
        self.root.iconbitmap(r"ico.ico")
        
        # Data files
        self.food_db_file = "nutrition_data.json"
        self.template_file = "template.html"
        self.output_pdf = "Nutrition_Plan.pdf"
        self.logo_path = "Logo.png"  # Default logo path
        self.last_save_version = None
        
        # Load data
        self.food_db = self.load_food_db()
        self.meal_plan = {
            "breakfast": [], "snack1": [], "lunch": [], 
            "pre_workout": [], "dinner": [], "night_snack": [],
            "calories": {"total": "0 سعرة حرارية", "protein": "0 جرام", "fat": "0 جرام", "carbs": "0 جرام", "water": "0 مل"},
            "supplements": [],
            "notes": [
                "التزم بمواعيد الوجبات قدر المستطاع",
                "احرص على شرب كمية المياه المحددة يومياً",
                "يمكنك تبديل البروتينات حسب البدائل المذكورة",
                "تجنب السكريات المضافة والأطعمة المصنعة و المياه الغازيه",
                "احصل على قسط كافٍ من النوم (7-8 ساعات يومياً)"
            ],
            "client_info": {"weight": 0, "water_intake": "0 مل"}
        }
        
        # Create UI
        self.create_widgets()
        self.setup_keyboard_shortcuts()
        self.update_food_list()
        self.update_meal_plan_display()
    
    def load_food_db(self):
        if os.path.exists(self.food_db_file):
            try:
                with open(self.food_db_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load food database: {str(e)}")
                return []
        return []
    
    def save_food_db(self):
        with open(self.food_db_file, "w", encoding="utf-8") as f:
            json.dump(self.food_db, f, ensure_ascii=False, indent=2)
    
    def create_widgets(self):
        # Configure style for modern look
        style = ttk.Style()
        style.configure("TFrame", background="#f0f0f0")
        style.configure("TLabel", background="#f0f0f0")
        style.configure("TButton", padding=5)
        style.configure("TEntry", padding=5)
        
        # Main frames
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Client info frame
        client_frame = ttk.LabelFrame(main_frame, text="Client Information", padding=10)
        client_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        # Weight entry
        ttk.Label(client_frame, text="Weight (kg):").grid(row=0, column=0, sticky="e")
        self.weight_var = tk.StringVar()
        weight_entry = ttk.Entry(client_frame, textvariable=self.weight_var, width=10)
        weight_entry.grid(row=0, column=1, padx=5)
        weight_entry.bind("<Return>", lambda e: self.calculate_water())
        ttk.Button(client_frame, text="Calculate Water", command=self.calculate_water).grid(row=0, column=2, padx=5)
        
        # Water intake display
        ttk.Label(client_frame, text="Water Intake:").grid(row=1, column=0, sticky="e")
        self.water_label = ttk.Label(client_frame, text="0 مل")
        self.water_label.grid(row=1, column=1, sticky="w")
        
        # Logo selection
        ttk.Button(client_frame, text="Select Logo", command=self.select_logo).grid(row=2, column=0, columnspan=3, pady=5)
        
        # Food database frame
        db_frame = ttk.LabelFrame(main_frame, text="Food Database", padding=10)
        db_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        
        # Search box
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(db_frame, textvariable=self.search_var)
        search_entry.pack(fill=tk.X)
        search_entry.bind("<Down>", lambda e: self.focus_next_widget(e, self.food_list))
        self.search_var.trace("w", lambda *args: self.update_food_list())
        
        # Food list with scrollbar
        food_list_frame = ttk.Frame(db_frame)
        food_list_frame.pack(fill=tk.BOTH, expand=True)
        
        self.food_list = tk.Listbox(food_list_frame, height=15, width=30)
        scrollbar = ttk.Scrollbar(food_list_frame, orient="vertical", command=self.food_list.yview)
        self.food_list.configure(yscrollcommand=scrollbar.set)
        
        self.food_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.food_list.bind("<<ListboxSelect>>", self.show_food_details)
        self.food_list.bind("<Double-Button-1>", self.add_selected_to_current_meal)
        self.food_list.bind("<Return>", self.add_selected_to_current_meal)
        
        # Food details and edit controls
        details_frame = ttk.Frame(db_frame)
        details_frame.pack(fill=tk.X, pady=5)
        
        self.food_details = tk.Text(details_frame, height=6, width=30)
        self.food_details.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        edit_btn_frame = ttk.Frame(details_frame)
        edit_btn_frame.pack(side=tk.RIGHT, padx=5)
        
        ttk.Button(edit_btn_frame, text="Edit", command=self.edit_selected_food).pack(pady=2)
        ttk.Button(edit_btn_frame, text="Delete", command=self.delete_selected_food).pack(pady=2)
        
        # Meal plan frame
        plan_frame = ttk.LabelFrame(main_frame, text="Meal Plan", padding=10)
        plan_frame.grid(row=0, column=1, rowspan=2, sticky="nsew", padx=5, pady=5)
        
        # Meal tabs
        self.notebook = ttk.Notebook(plan_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        self.meal_tabs = {}
        self.meal_lists = {}
        self.quantity_vars = {}
        
        meals = [
            ("breakfast", "☀️ الفطار (8:00 — 9:00 صباحًا)"),
            ("snack1", "🕚 سناك خفيف (11:00 — 12:00 ظهرًا)"),
            ("lunch", "🍽️ الغداء (قبل التمرين بساعتين)"),
            ("pre_workout", "🕧 قبل التمرين بنصف ساعة"),
            ("dinner", "🌙 العشاء (بعد التمرين مباشرة)"),
            ("night_snack", "🌜 سناك ليلي")
        ]
        
        for meal_id, meal_name in meals:
            tab = ttk.Frame(self.notebook)
            self.notebook.add(tab, text=meal_name)
            self.meal_tabs[meal_id] = tab
            
            # Meal item list with scrollbar
            list_frame = ttk.Frame(tab)
            list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            
            meal_list = tk.Listbox(list_frame, height=10)
            scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=meal_list.yview)
            meal_list.configure(yscrollcommand=scrollbar.set)
            
            meal_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            self.meal_lists[meal_id] = meal_list
            
            # Controls frame
            controls = ttk.Frame(tab)
            controls.pack(fill=tk.X, pady=5)
            
            # Quantity entry
            ttk.Label(controls, text="Quantity (g):").pack(side=tk.LEFT)
            self.quantity_vars[meal_id] = tk.StringVar(value="100")
            quantity_entry = ttk.Entry(controls, textvariable=self.quantity_vars[meal_id], width=8)
            quantity_entry.pack(side=tk.LEFT, padx=5)
            quantity_entry.bind("<Return>", lambda e, m=meal_id: self.add_to_meal(m))
            quantity_entry.bind("<Down>", lambda e: self.focus_next_widget(e, self.meal_lists[meal_id]))
            
            # Add button
            ttk.Button(controls, text="Add", command=lambda m=meal_id: self.add_to_meal(m)).pack(side=tk.LEFT)
            
            # Remove button
            ttk.Button(controls, text="Remove", command=lambda m=meal_id: self.remove_from_meal(m)).pack(side=tk.LEFT, padx=5)
        
        # Supplements frame
        supplements_frame = ttk.LabelFrame(plan_frame, text="Supplements", padding=10)
        supplements_frame.pack(fill=tk.X, pady=5)
        
        self.supplements_list = tk.Listbox(supplements_frame, height=4)
        self.supplements_list.pack(fill=tk.X)
        
        supp_controls = ttk.Frame(supplements_frame)
        supp_controls.pack(fill=tk.X, pady=5)
        
        self.supplement_name_var = tk.StringVar()
        supp_name_entry = ttk.Entry(supp_controls, textvariable=self.supplement_name_var, width=20)
        supp_name_entry.pack(side=tk.LEFT, padx=5)
        supp_name_entry.bind("<Return>", lambda e: self.add_supplement())
        supp_name_entry.bind("<Down>", lambda e: self.focus_next_widget(e, self.supplements_list))
        
        self.supplement_serving_var = tk.StringVar()
        ttk.Entry(supp_controls, textvariable=self.supplement_serving_var, width=10).pack(side=tk.LEFT, padx=5)
        ttk.Button(supp_controls, text="Add", command=self.add_supplement).pack(side=tk.LEFT)
        ttk.Button(supp_controls, text="Remove", command=self.remove_supplement).pack(side=tk.LEFT, padx=5)
        
        # Nutrition summary
        summary_frame = ttk.LabelFrame(plan_frame, text="Nutrition Summary", padding=10)
        summary_frame.pack(fill=tk.X, pady=5)
        
        self.summary_text = tk.Text(summary_frame, height=6)
        self.summary_text.pack(fill=tk.X)
        
        # Action buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=2, column=0, columnspan=2, pady=10)
        
        ttk.Button(btn_frame, text="Generate PDF", command=self.generate_pdf).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Save Plan", command=self.save_plan).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Load Plan", command=self.load_plan).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Add New Food", command=self.add_new_food).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Save Last Version", command=self.save_last_version).pack(side=tk.LEFT, padx=5)
        
        # Configure grid weights
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=2)
        main_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
    
    def setup_keyboard_shortcuts(self):
        # Delete key for food database
        self.food_list.bind("<Delete>", lambda e: self.delete_selected_food())
        
        # Delete key for meal lists
        for meal_id in self.meal_lists:
            self.meal_lists[meal_id].bind("<Delete>", lambda e, m=meal_id: self.remove_from_meal(m))
        
        # Delete key for supplements
        self.supplements_list.bind("<Delete>", lambda e: self.remove_supplement())
        
        # Ctrl+S to save
        self.root.bind("<Control-s>", lambda e: self.save_plan())
        
        # Ctrl+L to load
        self.root.bind("<Control-l>", lambda e: self.load_plan())
        
        # Ctrl+P to generate PDF
        self.root.bind("<Control-p>", lambda e: self.generate_pdf())
        
        # Ctrl+V to save last version
        self.root.bind("<Control-v>", lambda e: self.save_last_version())
        
        # Arrow key navigation
        self.root.bind("<Up>", self.focus_previous_widget)
        self.root.bind("<Down>", self.focus_next_widget)
    
    def focus_next_widget(self, event=None, target=None):
        if target:
            target.focus_set()
            if hasattr(target, "selection_clear"):
                target.selection_clear(0, tk.END)
                target.selection_set(0)
                target.activate(0)
            return "break"
        
        current_widget = self.root.focus_get()
        if not current_widget:
            return
        
        all_widgets = self.get_focusable_widgets()
        try:
            idx = all_widgets.index(current_widget)
            next_idx = (idx + 1) % len(all_widgets)
            all_widgets[next_idx].focus_set()
            
            # Special handling for Listbox widgets
            if isinstance(all_widgets[next_idx], tk.Listbox):
                all_widgets[next_idx].selection_clear(0, tk.END)
                all_widgets[next_idx].selection_set(0)
                all_widgets[next_idx].activate(0)
        except ValueError:
            pass
        
        return "break"
    
    def focus_previous_widget(self, event=None):
        current_widget = self.root.focus_get()
        if not current_widget:
            return
        
        all_widgets = self.get_focusable_widgets()
        try:
            idx = all_widgets.index(current_widget)
            prev_idx = (idx - 1) % len(all_widgets)
            all_widgets[prev_idx].focus_set()
            
            # Special handling for Listbox widgets
            if isinstance(all_widgets[prev_idx], tk.Listbox):
                all_widgets[prev_idx].selection_clear(0, tk.END)
                all_widgets[prev_idx].selection_set(0)
                all_widgets[prev_idx].activate(0)
        except ValueError:
            pass
        
        return "break"
    
    def get_focusable_widgets(self):
        """Return a list of all focusable widgets in tab order"""
        widgets = []
        
        # Client info widgets
        widgets.append(self.root.nametowidget(self.weight_var._name))
        widgets.append(self.water_label.master.children['!button'])  # Calculate Water button
        widgets.append(self.water_label.master.children['!button2'])  # Select Logo button
        
        # Food database widgets
        widgets.append(self.root.nametowidget(self.search_var._name))
        widgets.append(self.food_list)
        widgets.append(self.food_details)
        
        # Meal plan widgets (focus on current tab)
        current_tab = self.notebook.nametowidget(self.notebook.select())
        for child in current_tab.winfo_children():
            if isinstance(child, tk.Listbox):
                widgets.append(child)
            elif isinstance(child, ttk.Frame):
                for subchild in child.winfo_children():
                    if isinstance(subchild, ttk.Entry):
                        widgets.append(subchild)
        
        # Supplements widgets
        widgets.append(self.root.nametowidget(self.supplement_name_var._name))
        widgets.append(self.root.nametowidget(self.supplement_serving_var._name))
        widgets.append(self.supplements_list)
        
        return widgets
    
    def select_logo(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Image files", "*.png;*.jpg;*.jpeg")]
        )
        if file_path:
            self.logo_path = file_path
            messagebox.showinfo("Success", "Logo selected successfully")
    
    def calculate_water(self):
        try:
            weight = float(self.weight_var.get())
            if weight <= 0:
                raise ValueError
            
            # Calculate water intake: weight * 0.033 + 0.5 liters
            water_ml = (weight * 0.033 * 1000) + 500
            water_str = f"{water_ml:.0f} مل"
            
            self.water_label.config(text=water_str)
            self.meal_plan["client_info"]["weight"] = weight
            self.meal_plan["client_info"]["water_intake"] = water_str
            self.meal_plan["calories"]["water"] = water_str
            
            self.update_meal_plan_display()
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid weight (positive number)")
    
    def update_food_list(self):
        self.food_list.delete(0, tk.END)
        search_term = self.search_var.get().lower()
        
        for food in sorted(self.food_db, key=lambda x: x["name"]):
            if search_term in food["name"].lower():
                self.food_list.insert(tk.END, food["name"])
    
    def show_food_details(self, event):
        selection = self.food_list.curselection()
        if not selection:
            return
            
        food_name = self.food_list.get(selection[0])
        food = next((f for f in self.food_db if f["name"] == food_name), None)
        
        if food:
            details = (
                f"Name: {food['name']}\n"
                f"Calories: {food['calories']} kcal/100g\n"
                f"Protein: {food['protein']}g/100g\n"
                f"Carbs: {food['carbs']}g/100g\n"
                f"Fat: {food['fat']}g/100g\n"
                f"Serving: {food.get('serving', 'N/A')}"
            )
            self.food_details.delete(1.0, tk.END)
            self.food_details.insert(tk.END, details)
    
    def add_selected_to_current_meal(self, event):
        current_tab = self.notebook.tab(self.notebook.select(), "text")
        meal_id = next((k for k, v in self.meal_tabs.items() if v == self.notebook.nametowidget(self.notebook.select())), None)
        
        if meal_id:
            self.add_to_meal(meal_id)
    
    def add_to_meal(self, meal_id):
        selection = self.food_list.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a food item")
            return
            
        try:
            quantity = float(self.quantity_vars[meal_id].get())
            if quantity <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid quantity (positive number)")
            return
            
        food_name = self.food_list.get(selection[0])
        food = next((f for f in self.food_db if f["name"] == food_name), None)
        
        if food:
            # Calculate nutrition for the specified quantity
            calories = food["calories"] * quantity / 100
            protein = food["protein"] * quantity / 100
            carbs = food["carbs"] * quantity / 100
            fat = food["fat"] * quantity / 100
            
            # Show nutrition info for the specified quantity
            quantity_info = (
                f"For {quantity}g:\n"
                f"Calories: {calories:.1f} kcal\n"
                f"Protein: {protein:.1f}g\n"
                f"Carbs: {carbs:.1f}g\n"
                f"Fat: {fat:.1f}g"
            )
            messagebox.showinfo("Nutrition Info", quantity_info)
            
            # Add to meal plan
            self.meal_plan[meal_id].append({
                "name": food["name"],
                "quantity": quantity,
                "calories": calories,
                "protein": protein,
                "carbs": carbs,
                "fat": fat,
                "serving": food.get("serving", "")
            })
            
            # Update display
            self.update_meal_plan_display()
    
    def remove_from_meal(self, meal_id):
        selection = self.meal_lists[meal_id].curselection()
        if not selection:
            return
            
        # Remove from meal plan
        del self.meal_plan[meal_id][selection[0]]
        
        # Update display
        self.update_meal_plan_display()
    
    def add_supplement(self):
        supplement = self.supplement_name_var.get().strip()
        if not supplement:
            messagebox.showwarning("Warning", "Please enter a supplement name")
            return
        
        serving = self.supplement_serving_var.get().strip()
        if serving:
            supplement += f" ({serving})"
            
        self.meal_plan["supplements"].append(supplement)
        self.supplement_name_var.set("")
        self.supplement_serving_var.set("")
        self.update_supplements_list()
    
    def remove_supplement(self):
        selection = self.supplements_list.curselection()
        if not selection:
            return
            
        del self.meal_plan["supplements"][selection[0]]
        self.update_supplements_list()
    
    def update_supplements_list(self):
        self.supplements_list.delete(0, tk.END)
        for supp in self.meal_plan["supplements"]:
            self.supplements_list.insert(tk.END, supp)
    
    def update_meal_plan_display(self):
        # Update all meal lists
        for meal_id, meal_list in self.meal_lists.items():
            meal_list.delete(0, tk.END)
            for item in self.meal_plan[meal_id]:
                meal_list.insert(tk.END, f"{item['name']} - {item['quantity']}g")
        
        # Update supplements list
        self.update_supplements_list()
        
        # Update nutrition summary
        total_calories = 0
        total_protein = 0
        total_carbs = 0
        total_fat = 0
        
        # Calculate totals only from meal lists
        for meal_id in ["breakfast", "snack1", "lunch", "pre_workout", "dinner", "night_snack"]:
            for item in self.meal_plan[meal_id]:
                total_calories += item["calories"]
                total_protein += item["protein"]
                total_carbs += item["carbs"]
                total_fat += item["fat"]
        
        summary = (
            f"Total Calories: {total_calories:.0f} kcal\n"
            f"Protein: {total_protein:.1f}g\n"
            f"Carbs: {total_carbs:.1f}g\n"
            f"Fat: {total_fat:.1f}g\n"
            f"Water: {self.meal_plan['client_info']['water_intake']}"
        )
        
        self.summary_text.delete(1.0, tk.END)
        self.summary_text.insert(tk.END, summary)
        
        # Update plan data
        self.meal_plan["calories"] = {
            "total": f"{total_calories:.0f} سعرة حرارية",
            "protein": f"{total_protein:.0f} جرام",
            "fat": f"{total_fat:.0f} جرام",
            "carbs": f"{total_carbs:.0f} جرام",
            "water": self.meal_plan["client_info"]["water_intake"]
        }
    
    def edit_selected_food(self):
        selection = self.food_list.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a food item to edit")
            return
            
        food_name = self.food_list.get(selection[0])
        food = next((f for f in self.food_db if f["name"] == food_name), None)
        
        if food:
            self.edit_food_dialog(food, selection[0])
    
    def edit_food_dialog(self, food, index):
        edit_window = tk.Toplevel(self.root)
        edit_window.title("Edit Food Item")
        
        # Form fields
        fields = [
            ("name", "Food Name:"),
            ("calories", "Calories (per 100g):"),
            ("protein", "Protein (g per 100g):"),
            ("carbs", "Carbs (g per 100g):"),
            ("fat", "Fat (g per 100g):"),
            ("serving", "Serving Size:")
        ]
        
        entries = {}
        for i, (field, label) in enumerate(fields):
            ttk.Label(edit_window, text=label).grid(row=i, column=0, padx=5, pady=2, sticky="e")
            entry = ttk.Entry(edit_window)
            entry.grid(row=i, column=1, padx=5, pady=2)
            entry.insert(0, str(food.get(field, "")))
            entries[field] = entry
        
        # Save button
        ttk.Button(edit_window, text="Save", 
                 command=lambda: self.save_food_edit(food, index, entries, edit_window)).grid(row=len(fields), columnspan=2, pady=10)
    
    def save_food_edit(self, food, index, entries, window):
        try:
            updated_food = {
                "name": entries["name"].get(),
                "calories": float(entries["calories"].get()),
                "protein": float(entries["protein"].get()),
                "carbs": float(entries["carbs"].get()),
                "fat": float(entries["fat"].get()),
                "serving": entries["serving"].get()
            }
            
            # Update the food database
            self.food_db[index] = updated_food
            self.save_food_db()
            
            # Update the UI
            self.update_food_list()
            window.destroy()
            
            messagebox.showinfo("Success", "Food item updated successfully")
        except ValueError:
            messagebox.showerror("Error", "Please enter valid numbers for nutrition values")
    
    def delete_selected_food(self):
        selection = self.food_list.curselection()
        if not selection:
            return
            
        food_name = self.food_list.get(selection[0])
        if messagebox.askyesno("Confirm Delete", f"Delete {food_name} from database?"):
            del self.food_db[selection[0]]
            self.save_food_db()
            self.update_food_list()
    
    def add_new_food(self):
        add_window = tk.Toplevel(self.root)
        add_window.title("Add New Food")
        
        # Form fields
        fields = [
            ("name", "Food Name:"),
            ("calories", "Calories (per 100g):"),
            ("protein", "Protein (g per 100g):"),
            ("carbs", "Carbs (g per 100g):"),
            ("fat", "Fat (g per 100g):"),
            ("serving", "Serving Size:")
        ]
        
        entries = {}
        for i, (field, label) in enumerate(fields):
            ttk.Label(add_window, text=label).grid(row=i, column=0, padx=5, pady=2, sticky="e")
            entry = ttk.Entry(add_window)
            entry.grid(row=i, column=1, padx=5, pady=2)
            entries[field] = entry
        
        # Add button
        ttk.Button(add_window, text="Add", 
                 command=lambda: self.save_new_food(entries, add_window)).grid(row=len(fields), columnspan=2, pady=10)
    
    def save_new_food(self, entries, window):
        try:
            new_food = {
                "name": entries["name"].get(),
                "calories": float(entries["calories"].get()),
                "protein": float(entries["protein"].get()),
                "carbs": float(entries["carbs"].get()),
                "fat": float(entries["fat"].get()),
                "serving": entries["serving"].get()
            }
            
            if not new_food["name"]:
                messagebox.showwarning("Warning", "Food name cannot be empty")
                return
                
            # Add to food database
            self.food_db.append(new_food)
            self.save_food_db()
            
            # Update the UI
            self.update_food_list()
            window.destroy()
            
            messagebox.showinfo("Success", "New food item added successfully")
        except ValueError:
            messagebox.showerror("Error", "Please enter valid numbers for nutrition values")
    
    def generate_pdf(self):
        # Generate HTML from template
        html_template = self.load_template()
        
        # Replace placeholders with meal plan data
        html_content = self.fill_template(html_template)
        
        # Generate PDF
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.output_pdf = f"Nutrition_Plan_{timestamp}.pdf"
            
            HTML(string=html_content).write_pdf(self.output_pdf)
            messagebox.showinfo("Success", f"PDF generated successfully: {self.output_pdf}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate PDF: {str(e)}")
    
    def load_template(self):
        # Same template as before
        return """<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
  <meta charset="UTF-8">
  <style>
    @page {
    size: 400pt 800pt;
    margin: 8pt;
    background-color: #2b0000;
    }

    html, body {
    margin: 1;
    background-color: #2b0000;
    font-family: "Cairo", "Segoe UI", Arial, sans-serif;
    font-weight: bold;
    color: white;
    font-size: 8pt;
    line-height: 1.2;
    box-sizing: border-box;
    height: 97.5%;
    }

    .logo {
      position: absolute;
      top: 1px;
      left: 10px;
      width: 70px;
      height: 35px;
    }

    h2 {
      text-align: center;
      color: #FFD700;
      font-size: 16pt;
      margin: 8px 0;
    }

    .frame {
    width: 100%;
    height: 100%;
    border: 2px solid #FFD700;
    border-radius: 8px;
    padding: 5px;
    box-sizing: border-box;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    }

    .meal-container, .calories-box, .supplements-box, .notes-box {
      margin-bottom: 10px;
    }

    .meal-title, .snack-title, .notes-title {
      color: #FFD700;
      margin-bottom: 12px;
      text-align: right;
      font-size: 9pt;
    }

    .meal-content, .notes-content {
      display: flex;
      background: linear-gradient(to right, #2b0000, #550000);
      border: 1px solid #FFD700;
      border-radius: 5px;
      padding: 3px;
    }

    .food-items {
      flex: 3;
      padding-right: 4px;
      border-right: 1px solid #AAA;
    }

    .quantity-table {
      flex: 1;
      padding-left: 4px;
    }

    .food-row, .note-row {
      display: flex;
      justify-content: space-between;
      margin-bottom: 1px;
    }

    .food-name, .note-text {
      text-align: right;
      color: #DDD;
    }

    .food-quantity {
      color: #FFD700;
      text-align: left;
    }

    .calories-box, .supplements-box, .notes-box {
      background: linear-gradient(to right, #2b0000, #550000);
      border: 1px solid #FFD700;
      border-radius: 5px;
      padding: 4px;
    }

    .calories-title, .supplements-title, .notes-title {
      color: #FFD700;
      text-align: center;
      margin-bottom: 3px;
      font-size: 10pt;
    }

    .calories-row, .supplement-row {
      display: flex;
      justify-content: space-between;
      margin: 2px 4px;
    }

    .calories-label, .supplement-label {
      color: #FFFFFF;
      font-size: 8pt;
    }

    .calories-value, .supplement-value {
      color: #FFD700;
    }

    .notes-content {
    flex-direction: column;
    padding: 5px;
    border: none;
    background: none;
    }

    .note-row {
    margin-bottom: 3px;
    display: list-item;
    list-style-type: disc;
    list-style-position: inside;
    }
    .footer-signature {
      text-align: center;
      margin-top: 8px;
      color: #FFD700;
      font-size: 8pt;
    }
  </style>
</head>
<body>
  <a href="https://www.instagram.com/elitefit.eg?igsh=MXFud2dyM3lqcnNuZQ==">
    <img src="file:{logo_path}" class="logo" alt="Elite Fit Logo">
  </a>
  <h2>نظامك الغذائي</h2>
  <div class="frame">
    {meals}
    {calories}
    {supplements}
    {notes}
    <div class="footer-signature">
      <div>𝗧𝗥𝗔𝗡𝗦𝗙𝗢𝗥𝗠 𝗔𝗡𝗬𝗪𝗛𝗘𝗥𝗘, 𝗔𝗡𝗬𝗧𝗜𝗠𝗘</div>
      <div style="margin-top: 1px;">Good Luck 💪 Stay Strong!</div>
    </div>
  </div>
</body>
</html>"""
    
    def fill_template(self, template):
        # Generate meals HTML
        meals_html = ""
        meal_templates = {
            "breakfast": "☀️ الفطار (8:00 — 9:00 صباحًا)",
            "snack1": "🕚 سناك خفيف (11:00 — 12:00 ظهرًا)",
            "lunch": "🍽️ الغداء (قبل التمرين بساعتين)",
            "pre_workout": "🕧 قبل التمرين بنصف ساعة",
            "dinner": "🌙 العشاء (بعد التمرين مباشرة)",
            "night_snack": "🌜 سناك ليلي"
        }
        
        for meal_id, meal_title in meal_templates.items():
            if self.meal_plan[meal_id]:
                meals_html += f"""
                <div class="meal-container">
                  <div class="meal-title">{meal_title}</div>
                  <div class="meal-content">
                    <div class="food-items">"""
                
                for item in self.meal_plan[meal_id]:
                    meals_html += f"""
                      <div class="food-row"><span class="food-name">{item['quantity']}g {item['name']}</span></div>"""
                
                meals_html += """
                    </div>
                    <div class="quantity-table">
                """
                
                for item in self.meal_plan[meal_id]:
                    meals_html += """
                      <div class="food-row"><span class="food-quantity"></span></div>"""
                
                meals_html += """
                    </div>
                  </div>
                </div>"""
        
        # Generate calories HTML
        calories_html = f"""
        <div class="calories-box">
          <div class="calories-title">السعرات الحرارية</div>
          <div class="calories-row"><span class="calories-label">السعرات</span><span class="calories-value">{self.meal_plan['calories']['total']}</span></div>
          <div class="calories-row"><span class="calories-label">البروتين</span><span class="calories-value">{self.meal_plan['calories']['protein']}</span></div>
          <div class="calories-row"><span class="calories-label">الدهون</span><span class="calories-value">{self.meal_plan['calories']['fat']}</span></div>
          <div class="calories-row"><span class="calories-label">الكاربوهيدرات</span><span class="calories-value">{self.meal_plan['calories']['carbs']}</span></div>
          <div class="calories-row"><span class="calories-label">تشرب في اليوم مياه</span><span class="calories-value">{self.meal_plan['calories']['water']}</span></div>
        </div>"""
        
        # Generate supplements HTML
        supplements_html = """
        <div class="supplements-box">
          <div class="supplements-title">المكملات الغذائية</div>"""
        
        for supp in self.meal_plan["supplements"]:
            supplements_html += f"""
          <div class="supplement-row"><span class="supplement-label">{supp}</span></div>"""
        
        supplements_html += """
        </div>"""
        
        # Generate notes HTML
        notes_html = """
        <div class="notes-box">
          <div class="notes-title">نصائح لتحقيق أفضل النتائج</div>
          <div class="notes-content">"""
        
        for note in self.meal_plan["notes"]:
            notes_html += f"""
            <div class="note-row"><span class="note-text">{note}</span></div>"""
        
        notes_html += """
          </div>
        </div>"""
        
        # Replace placeholders
        html = template.replace("{logo_path}", self.logo_path)
        html = html.replace("{meals}", meals_html)
        html = html.replace("{calories}", calories_html)
        html = html.replace("{supplements}", supplements_html)
        html = html.replace("{notes}", notes_html)
        
        return html
    
    def save_plan(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")],
            initialfile="meal_plan.json"
        )
        
        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(self.meal_plan, f, ensure_ascii=False, indent=2)
                self.last_save_version = self.meal_plan.copy()
                messagebox.showinfo("Success", "Meal plan saved successfully")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save meal plan: {str(e)}")
    
    def save_last_version(self):
        if not self.last_save_version:
            messagebox.showwarning("Warning", "No previous version to save")
            return
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = f"meal_plan_backup_{timestamp}.json"
        
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(self.last_save_version, f, ensure_ascii=False, indent=2)
            messagebox.showinfo("Success", f"Last version saved as {file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save last version: {str(e)}")
    
    def load_plan(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json")]
        )
        
        if file_path:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    self.meal_plan = json.load(f)
                    self.last_save_version = self.meal_plan.copy()
                
                # Update UI elements
                self.weight_var.set(str(self.meal_plan["client_info"]["weight"]))
                self.water_label.config(text=self.meal_plan["client_info"]["water_intake"])
                
                self.update_meal_plan_display()
                messagebox.showinfo("Success", "Meal plan loaded successfully")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load meal plan: {str(e)}")

if __name__ == "__main__":
    # Sample food database if none exists
    sample_foods = [
        {
            "name": "بيض مسلوق",
            "calories": 155,
            "protein": 13,
            "carbs": 1.1,
            "fat": 11,
            "serving": "حبة كبيرة (50g)"
        },
        {
            "name": "شوفان",
            "calories": 389,
            "protein": 16.9,
            "carbs": 66.3,
            "fat": 6.9,
            "serving": "100g"
        },
        {
            "name": "صدور دجاج",
            "calories": 165,
            "protein": 31,
            "carbs": 0,
            "fat": 3.6,
            "serving": "100g"
        }
    ]
    
    if not os.path.exists("nutrition_data.json"):
        with open("nutrition_data.json", "w", encoding="utf-8") as f:
            json.dump(sample_foods, f, ensure_ascii=False, indent=2)
        
    root = tk.Tk()
    app = NutritionPlanCreator(root)
    root.mainloop()
