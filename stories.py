import os
import shutil
import flet as ft
from PIL import Image, ImageFilter, ImageDraw, ImageFont

# Configurações da imagem final
OUTPUT_WIDTH = 1080
OUTPUT_HEIGHT = 1920
OUTPUT_FILENAME = "versiculo.png"

# Pasta para armazenar uploads temporários
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Caminhos possíveis para encontrar uma fonte
FONT_PATHS_TO_TRY = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    "C:/Windows/Fonts/arial.ttf",
]

def find_font(paths):
    for p in paths:
        if os.path.exists(p):
            return p
    return None

FONT_PATH = find_font(FONT_PATHS_TO_TRY)

# Funções auxiliares
def get_text_size(draw, text, font):
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]

def wrap_text(draw, text, font, max_width):
    words = text.split()
    lines = []
    if not words:
        return [""]
    line = words[0]
    for w in words[1:]:
        test_line = f"{line} {w}"
        if get_text_size(draw, test_line, font)[0] <= max_width:
            line = test_line
        else:
            lines.append(line)
            line = w
    lines.append(line)
    return lines

# Função principal para criar a imagem
def create_story_image(message, sender, bg_path, output_path=OUTPUT_FILENAME):
    bg = Image.open(bg_path).convert("RGB")
    bg_ratio = bg.width / bg.height
    target_ratio = OUTPUT_WIDTH / OUTPUT_HEIGHT

    if bg_ratio > target_ratio:
        new_height = OUTPUT_HEIGHT
        new_width = int(bg_ratio * new_height)
    else:
        new_width = OUTPUT_WIDTH
        new_height = int(new_width / bg_ratio)

    bg_resized = bg.resize((new_width, new_height), Image.LANCZOS)
    left = (new_width - OUTPUT_WIDTH) // 2
    top = (new_height - OUTPUT_HEIGHT) // 2
    bg_cropped = bg_resized.crop((left, top, left + OUTPUT_WIDTH, top + OUTPUT_HEIGHT))
    bg_blurred = bg_cropped.filter(ImageFilter.GaussianBlur(radius=12))

    canvas = Image.new("RGB", (OUTPUT_WIDTH, OUTPUT_HEIGHT))
    canvas.paste(bg_blurred)
    draw = ImageDraw.Draw(canvas)

    if FONT_PATH:
        message_font = ImageFont.truetype(FONT_PATH, 80)
        sender_font = ImageFont.truetype(FONT_PATH, 40)
        footer_font = ImageFont.truetype(FONT_PATH, 30)
    else:
        message_font = sender_font = footer_font = ImageFont.load_default()

    margin_x = 80
    max_text_width = OUTPUT_WIDTH - 2 * margin_x
    lines = wrap_text(draw, message, message_font, max_text_width)

    line_height = get_text_size(draw, "Ay", message_font)[1] + 12
    total_text_height = line_height * len(lines)
    current_y = (OUTPUT_HEIGHT - total_text_height) // 2

    for line in lines:
        w, h = get_text_size(draw, line, message_font)
        x = (OUTPUT_WIDTH - w) // 2
        draw.text((x+3, current_y+3), line, font=message_font, fill=(0,0,0,180))
        draw.text((x, current_y), line, font=message_font, fill="white")
        current_y += line_height

    sender_text = f"— {sender}"
    sw, sh = get_text_size(draw, sender_text, sender_font)
    sx = (OUTPUT_WIDTH - sw) // 2
    sy = current_y + 20
    draw.text((sx+2, sy+2), sender_text, font=sender_font, fill=(0,0,0,180))
    draw.text((sx, sy), sender_text, font=sender_font, fill=(230,230,230))

    footer_text = "@elizeu.dev"
    fw, fh = get_text_size(draw, footer_text, footer_font)
    fx = (OUTPUT_WIDTH - fw) // 2
    fy = OUTPUT_HEIGHT - 60
    draw.text((fx+1, fy+1), footer_text, font=footer_font, fill=(0,0,0,180))
    draw.text((fx, fy), footer_text, font=footer_font, fill="white")

    canvas.save(output_path, "PNG")
    return output_path

# Aplicativo com Flet
def main(page: ft.Page):
    page.title = "Gerador de Imagens de Versículos - @elizeu.dev"
    page.scroll = ft.ScrollMode.AUTO

    bg_path = {"value": None}
    txt_message = ft.Ref[ft.TextField]()
    txt_sender = ft.Ref[ft.TextField]()
    lbl_bg = ft.Ref[ft.Text]()

    # Seleção da imagem de fundo
    def on_bg_selected(result: ft.FilePickerResultEvent):
        if result.files and len(result.files) > 0:
            uploaded_file = result.files[0]
            local_path = os.path.join(UPLOAD_DIR, uploaded_file.name)

            # No navegador, precisamos salvar os bytes manualmente
            if uploaded_file.path:
                shutil.copy(uploaded_file.path, local_path)
            elif uploaded_file.bytes_data:
                with open(local_path, "wb") as f:
                    f.write(uploaded_file.bytes_data)

            bg_path["value"] = local_path
            lbl_bg.current.value = uploaded_file.name
        else:
            lbl_bg.current.value = "Nenhuma imagem selecionada"
        page.update()

    def select_background(e):
        file_picker = ft.FilePicker(on_result=on_bg_selected)
        page.overlay.append(file_picker)
        page.update()
        file_picker.pick_files(allow_multiple=False, allowed_extensions=["png", "jpg", "jpeg", "webp"])

    # Salvamento da imagem gerada
    def on_save_selected(result: ft.FilePickerResultEvent, message, sender):
        if result.path:
            try:
                create_story_image(message, sender, bg_path["value"], result.path)
                page.dialog = ft.AlertDialog(title=ft.Text(f"Imagem salva em:\n{result.path}"))
                page.dialog.open = True
                page.update()
            except Exception as e:
                page.dialog = ft.AlertDialog(title=ft.Text(f"Erro: {str(e)}"))
                page.dialog.open = True
                page.update()

    # Geração da imagem
    def generate_image(e):
        message = txt_message.current.value.strip()
        sender = txt_sender.current.value.strip() or "Anônimo"

        if not message:
            page.dialog = ft.AlertDialog(title=ft.Text("Por favor, insira o versículo."))
            page.dialog.open = True
            page.update()
            return

        if not bg_path["value"]:
            page.dialog = ft.AlertDialog(title=ft.Text("Por favor, selecione uma imagem de fundo."))
            page.dialog.open = True
            page.update()
            return

        file_picker_save = ft.FilePicker(on_result=lambda r: on_save_selected(r, message, sender))
        page.overlay.append(file_picker_save)
        page.update()
        file_picker_save.save_file(file_name=OUTPUT_FILENAME, allowed_extensions=["png"])

    # Layout
    page.add(
        ft.Text("Texto do Versículo:", weight="bold"),
        ft.TextField(ref=txt_message, multiline=True, min_lines=4, max_lines=6, expand=True),
        ft.Text("Referência Bíblica:", weight="bold"),
        ft.TextField(ref=txt_sender),
        ft.Row([
            ft.Text("Nenhuma imagem selecionada", ref=lbl_bg, expand=True),
            ft.ElevatedButton("Selecionar imagem de fundo", on_click=select_background)
        ]),
        ft.Row([
            ft.ElevatedButton("Gerar Imagem", on_click=generate_image),
            ft.ElevatedButton("Sair", on_click=lambda e: page.window_close())
        ])
    )

if __name__ == "__main__":
    ft.app(target=main)
