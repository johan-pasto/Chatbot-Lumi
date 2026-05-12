import customtkinter as ctk
import requests

def enviar():

    texto = entrada.get()

    chat.insert("end", "Tú: " + texto + "\n")

    r = requests.post(
        "http://127.0.0.1:8000/chat",
        json={"texto": texto}
    )

    respuesta = r.json()["respuesta"]

    chat.insert("end", "Lumi: " + respuesta + "\n")

    entrada.delete(0, "end")


app = ctk.CTk()
app.title("Lumi 💙")

chat = ctk.CTkTextbox(app, width=500, height=400)
chat.pack(pady=10)

entrada = ctk.CTkEntry(app, width=400)
entrada.pack(side="left", padx=10)

boton = ctk.CTkButton(app, text="Enviar", command=enviar)
boton.pack(side="right", padx=10)

app.mainloop()