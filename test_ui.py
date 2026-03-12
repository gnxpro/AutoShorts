import customtkinter as ctk

app = ctk.CTk()
app.geometry("600x400")

label = ctk.CTkLabel(app, text="UI OK")
label.pack(pady=40)

app.mainloop()