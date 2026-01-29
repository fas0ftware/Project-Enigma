import customtkinter as ctk
import qrcode
from PIL import Image

# --- Aesthesius Configuration ---
ctk.set_appearance_mode("Dark")  # Aesthesius dark theme
ctk.set_default_color_theme("blue")  # Theme color

class ProjectEnigma(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Window Settings
        self.title("Aesthesius - Project Enigma")
        self.geometry("500x550")
        self.resizable(False, False)

        # Logo / Header
        self.header_label = ctk.CTkLabel(self, text="PROJECT ENIGMA", font=("Roboto", 24, "bold"))
        self.header_label.pack(pady=20)

        # Data Entry Field
        self.entry = ctk.CTkEntry(self, placeholder_text="Enter link or text for QR Code...", width=350)
        self.entry.pack(pady=10)

        # Generate Button
        self.generate_btn = ctk.CTkButton(self, text="Generate QR", command=self.generate_qr, width=200)
        self.generate_btn.pack(pady=10)

        # QR Code Display Area (Label)
        self.qr_label = ctk.CTkLabel(self, text="")
        self.qr_label.pack(pady=20)

        # Status Message
        self.status_label = ctk.CTkLabel(self, text="Ready", text_color="gray")
        self.status_label.pack(side="bottom", pady=10)

        # Save Button (Initially hidden)
        self.save_btn = ctk.CTkButton(self, text="Save Image", command=self.save_qr, width=200, fg_color="green")
        # This button will only appear after the QR is generated
        
        self.current_qr_image = None # Keep the generated image in memory

    def generate_qr(self):
        data = self.entry.get()
        
        if not data:
            self.status_label.configure(text="Please enter some data!", text_color="red")
            return

        try:
            # QR Code Configuration
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_H,
                box_size=10,
                border=2,
            )
            qr.add_data(data)
            qr.make(fit=True)

            # Create Image (Standard Black/White)
            img = qr.make_image(fill_color="black", back_color="white")
            self.current_qr_image = img # Store for saving

            # Convert to CTkImage for display
            ctk_img = ctk.CTkImage(light_image=img.get_image(), dark_image=img.get_image(), size=(250, 250))
            
            self.qr_label.configure(image=ctk_img, text="") # Clear text, set image
            self.save_btn.pack(pady=10) # Make save button visible
            self.status_label.configure(text="QR Code generated successfully.", text_color="white")

        except Exception as e:
            self.status_label.configure(text=f"Error: {str(e)}", text_color="red")

    def save_qr(self):
        if self.current_qr_image:
            try:
                # Filename can be dynamic later. For now, it's static.
                filename = "enigma_qr.png"
                self.current_qr_image.save(filename)
                self.status_label.configure(text=f"Saved: {filename}", text_color="#00FF00")
            except Exception as e:
                self.status_label.configure(text=f"Save Error: {str(e)}", text_color="red")

if __name__ == "__main__":
    app = ProjectEnigma()
    app.mainloop()