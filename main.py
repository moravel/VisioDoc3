from visiodoc_app import VisioDoc3

# This is the main entry point for the VisioDoc3 application.
# C'est le point d'entrée principal de l'application VisioDoc3.
if __name__ == "__main__":
    # Create an instance of the VisioDoc3 application.
    # Crée une instance de l'application VisioDoc3.
    app = VisioDoc3()
    # Start the Tkinter event loop, which keeps the application running.
    # Démarre la boucle d'événements Tkinter, qui maintient l'application en cours d'exécution.
    app.mainloop()