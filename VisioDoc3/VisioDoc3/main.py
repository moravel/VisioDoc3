from visiodoc_app import VisioDoc3
import pyi_splash

if __name__ == "__main__":
    app = VisioDoc3()
    pyi_splash.close()
    app.mainloop()