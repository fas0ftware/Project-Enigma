"""Project Enigma: desktop QR code generator (CustomTkinter). The logic lives in enigma_core.py."""

from tkinter import colorchooser, filedialog

import customtkinter as ctk

import enigma_core as core

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

KINDS = ("Text / URL", "Wi-Fi", "Contact", "E-mail")


class ProjectEnigma(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(f"FA Software - Project Enigma {core.__version__}")
        self.geometry("560x780")
        self.resizable(False, False)
        self.image = None
        self.data = ""
        self.style = core.Style()

        ctk.CTkLabel(self, text="PROJECT ENIGMA", font=("Roboto", 24, "bold")).pack(pady=(18, 6))
        self.kind = ctk.CTkSegmentedButton(self, values=list(KINDS), command=self.show_fields)
        self.kind.set(KINDS[0])
        self.kind.pack(pady=6)

        self.fields_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.fields_frame.pack(pady=6)
        self.inputs: dict[str, ctk.CTkEntry] = {}
        self.show_fields(KINDS[0])

        options = ctk.CTkFrame(self, fg_color="transparent")
        options.pack(pady=6)
        self.fg_btn = ctk.CTkButton(options, text="Colour", width=110, command=lambda: self.pick("fg"))
        self.bg_btn = ctk.CTkButton(options, text="Background", width=110, command=lambda: self.pick("bg"))
        self.logo_btn = ctk.CTkButton(options, text="Logo…", width=110, command=self.pick_logo)
        for b in (self.fg_btn, self.bg_btn, self.logo_btn):
            b.pack(side="left", padx=4)

        ctk.CTkButton(self, text="Generate QR", command=self.generate, width=220).pack(pady=8)
        self.preview = ctk.CTkLabel(self, text="")
        self.preview.pack(pady=8)
        self.save_btn = ctk.CTkButton(self, text="Save as PNG / SVG…", command=self.save, width=220, fg_color="green")
        self.status = ctk.CTkLabel(self, text="Ready", text_color="gray")
        self.status.pack(side="bottom", pady=10)

    # --- form -----------------------------------------------------------------------------
    def show_fields(self, kind):
        for child in self.fields_frame.winfo_children():
            child.destroy()
        fields = {
            "Text / URL": [("data", "Link or text")],
            "Wi-Fi": [("ssid", "Network name (SSID)"), ("password", "Password")],
            "Contact": [("name", "Full name"), ("phone", "Phone"), ("email", "E-mail")],
            "E-mail": [("to", "To"), ("subject", "Subject")],
        }[kind]
        self.inputs = {}
        for key, label in fields:
            entry = ctk.CTkEntry(self.fields_frame, placeholder_text=label, width=380,
                                 show="•" if key == "password" else "")
            entry.pack(pady=4)
            self.inputs[key] = entry

    def value(self, key):
        return self.inputs[key].get().strip() if key in self.inputs else ""

    def payload(self):
        kind = self.kind.get()
        if kind == "Wi-Fi":
            return core.wifi_payload(self.value("ssid"), self.value("password"))
        if kind == "Contact":
            return core.vcard_payload(self.value("name"), self.value("phone"), self.value("email"))
        if kind == "E-mail":
            return core.email_payload(self.value("to"), self.value("subject"))
        return self.value("data")

    def pick(self, which):
        colour = colorchooser.askcolor(title="Choose a colour")[1]
        if colour:
            setattr(self.style, which, colour)
            self.status.configure(text=f"{'Colour' if which == 'fg' else 'Background'}: {colour}", text_color="white")

    def pick_logo(self):
        path = filedialog.askopenfilename(filetypes=[("Images", "*.png *.jpg *.jpeg *.webp")])
        self.style.logo = path or None
        self.status.configure(text=f"Logo: {path}" if path else "No logo", text_color="white")

    # --- actions --------------------------------------------------------------------------
    def generate(self):
        try:
            self.data = self.payload()
            self.image = core.make_qr(self.data, self.style)
        except (ValueError, OSError) as exc:
            self.status.configure(text=str(exc), text_color="red")
            return
        preview = ctk.CTkImage(light_image=self.image, dark_image=self.image, size=(300, 300))
        self.preview.configure(image=preview, text="")
        self.save_btn.pack(pady=8)
        self.status.configure(text="QR code generated.", text_color="white")

    def save(self):
        if self.image is None:
            return
        path = filedialog.asksaveasfilename(defaultextension=".png", initialfile="enigma_qr.png",
                                            filetypes=[("PNG image", "*.png"), ("SVG vector", "*.svg")])
        if not path:
            return
        try:
            if path.lower().endswith(".svg"):
                if self.style.logo:
                    raise ValueError("SVG export does not include the logo; save as PNG instead")
                with open(path, "w", encoding="utf-8") as fh:
                    fh.write(core.make_svg(self.data, self.style))
            else:
                self.image.save(path)
            self.status.configure(text=f"Saved: {path}", text_color="#00FF00")
        except (ValueError, OSError) as exc:
            self.status.configure(text=f"Save error: {exc}", text_color="red")


if __name__ == "__main__":
    ProjectEnigma().mainloop()
