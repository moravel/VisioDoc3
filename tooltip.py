import tkinter as tk

# Tooltip class for displaying hover information over widgets.
# Classe Tooltip pour afficher des informations au survol des widgets.
class Tooltip:
    def __init__(self, widget, text):
        """
        Initializes a Tooltip object.
        Initialise un objet Tooltip.

        Args:
            widget (tk.Widget): The Tkinter widget to attach the tooltip to.
                                Le widget Tkinter auquel attacher l'info-bulle.
            text (str): The text to display in the tooltip.
                        Le texte à afficher dans l'info-bulle.
        """
        self.widget = widget
        self.text = text
        self.tooltip_window = None # The Toplevel window for the tooltip / La fenêtre Toplevel pour l'info-bulle
        self.id = None # ID for the scheduled 'show_tooltip' event / ID pour l'événement 'show_tooltip' planifié
        
        # Bind mouse enter and leave events to show/hide the tooltip
        # Lie les événements d'entrée et de sortie de la souris pour afficher/masquer l'info-bulle
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)

    def show_tooltip(self, event=None):
        """
        Schedules the tooltip to be shown after a delay.
        Planifie l'affichage de l'info-bulle après un délai.
        """
        # Cancel any existing scheduled show event to prevent multiple tooltips
        # Annule tout événement d'affichage planifié existant pour éviter les info-bulles multiples
        if self.id:
            self.widget.after_cancel(self.id)
        # Schedule the _show_tooltip_after_delay method to run after 500ms
        # Planifie l'exécution de la méthode _show_tooltip_after_delay après 500 ms
        self.id = self.widget.after(500, self._show_tooltip_after_delay)

    def _show_tooltip_after_delay(self):
        """
        Creates and displays the tooltip window.
        Crée et affiche la fenêtre de l'info-bulle.
        """
        # Create a new top-level window for the tooltip
        # Crée une nouvelle fenêtre de niveau supérieur pour l'info-bulle
        self.tooltip_window = tk.Toplevel(self.widget)
        # Remove window decorations (title bar, borders)
        # Supprime les décorations de la fenêtre (barre de titre, bordures)
        self.tooltip_window.wm_overrideredirect(True)
        # Set a temporary geometry to allow winfo_width/height to work correctly later
        # Définit une géométrie temporaire pour permettre à winfo_width/height de fonctionner correctement plus tard
        self.tooltip_window.wm_geometry("+0+0")

        # Create a label to display the tooltip text
        # Crée une étiquette pour afficher le texte de l'info-bulle
        label = tk.Label(self.tooltip_window,
                         text=self.text,
                         background="#FFFFEA", # Light yellow background / Fond jaune clair
                         relief="solid", # Solid border / Bordure solide
                         borderwidth=1,
                         font=("tahoma", "8", "normal"))
        label.pack(padx=1) # Add a small padding inside the label / Ajoute un petit rembourrage à l'intérieur de l'étiquette

        # Force the tooltip window to update its geometry so winfo_width/height return correct values
        # Force la fenêtre de l'info-bulle à mettre à jour sa géométrie afin que winfo_width/height renvoie des valeurs correctes
        self.tooltip_window.update_idletasks()

        # Get widget's absolute position and size on screen
        # Obtient la position et la taille absolues du widget à l'écran
        x = self.widget.winfo_rootx()
        y = self.widget.winfo_rooty()
        width = self.widget.winfo_width()
        height = self.widget.winfo_height()

        # Calculate tooltip position (initially below the widget)
        # Calcule la position de l'info-bulle (initialement sous le widget)
        tooltip_x = x
        tooltip_y = y + height + 5 # 5 pixels below the widget / 5 pixels sous le widget

        # Get screen dimensions to prevent tooltip from going off-screen
        # Obtient les dimensions de l'écran pour empêcher l'info-bulle de sortir de l'écran
        screen_width = self.widget.winfo_screenwidth()
        screen_height = self.widget.winfo_screenheight()

        # Get tooltip dimensions
        # Obtient les dimensions de l'info-bulle
        tooltip_width = self.tooltip_window.winfo_width()
        tooltip_height = self.tooltip_window.winfo_height()

        # Adjust tooltip_x if it goes off-screen to the right
        # Ajuste tooltip_x s'il sort de l'écran à droite
        if tooltip_x + tooltip_width > screen_width:
            tooltip_x = screen_width - tooltip_width - 5 # 5 pixels padding from right edge / 5 pixels de rembourrage du bord droit

        # Adjust tooltip_y if it goes off-screen to the bottom (display above instead)
        # Ajuste tooltip_y s'il sort de l'écran en bas (affiche au-dessus à la place)
        if tooltip_y + tooltip_height > screen_height:
            tooltip_y = y - tooltip_height - 5 # Display above the widget if no space below / Affiche au-dessus du widget s'il n'y a pas d'espace en dessous

        # Ensure tooltip_x is not negative (off-screen to the left)
        # S'assure que tooltip_x n'est pas négatif (hors écran à gauche)
        if tooltip_x < 0:
            tooltip_x = 0

        # Ensure tooltip_y is not negative (off-screen to the top)
        # S'assure que tooltip_y n'est pas négatif (hors écran en haut)
        if tooltip_y < 0:
            tooltip_y = 0

        # Set the final geometry of the tooltip window
        # Définit la géométrie finale de la fenêtre de l'info-bulle
        self.tooltip_window.wm_geometry(f"{tooltip_width}x{tooltip_height}+{tooltip_x}+{tooltip_y}")

    def hide_tooltip(self, event=None):
        """
        Hides and destroys the tooltip window.
        Masque et détruit la fenêtre de l'info-bulle.
        """
        # Cancel any pending show_tooltip event
        # Annule tout événement show_tooltip en attente
        if self.id:
            self.widget.after_cancel(self.id)
        # Destroy the tooltip window if it exists
        # Détruit la fenêtre de l'info-bulle si elle existe
        if self.tooltip_window:
            self.tooltip_window.destroy()
        self.tooltip_window = None
        self.id = None