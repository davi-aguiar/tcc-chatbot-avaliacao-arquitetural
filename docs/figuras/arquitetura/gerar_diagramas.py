"""Gera as duas figuras vetoriais e PNGs da arquitetura documentada."""
import math
import os
import xml.etree.ElementTree as ET
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
SCALE = 2
INK = "#202020"
ET.register_namespace("", "http://www.w3.org/2000/svg")
SVG_NS = "http://www.w3.org/2000/svg"


@lru_cache
def font(size, bold=False):
    fonts = Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts"
    return ImageFont.truetype(str(fonts / ("arialbd.ttf" if bold else "arial.ttf")), size * SCALE)


def tag(name):
    return f"{{{SVG_NS}}}{name}"


class Drawing:
    def __init__(self, width, height, title, description):
        self.width, self.height = width, height
        self.svg = ET.Element(tag("svg"), {
            "width": "160mm", "height": f"{height / width * 160:.3f}mm",
            "viewBox": f"0 0 {width} {height}", "role": "img",
            "aria-labelledby": "title description"})
        ET.SubElement(self.svg, tag("title"), {"id": "title"}).text = title
        ET.SubElement(self.svg, tag("desc"), {"id": "description"}).text = description
        self.image = Image.new("RGB", (width * SCALE, height * SCALE), "white")
        self.paint = ImageDraw.Draw(self.image)
        ET.SubElement(self.svg, tag("rect"), {
            "width": str(width), "height": str(height), "fill": "white"})

    def rect(self, x, y, width, height, fill="white", stroke=INK, radius=12, line=2):
        ET.SubElement(self.svg, tag("rect"), {
            "x": str(x), "y": str(y), "width": str(width), "height": str(height),
            "rx": str(radius), "fill": fill, "stroke": stroke, "stroke-width": str(line)})
        self.paint.rounded_rectangle(
            tuple(v * SCALE for v in (x, y, x + width, y + height)), radius * SCALE,
            fill=fill, outline=stroke, width=round(line * SCALE))

    def text(self, x, y, content, size=28, bold=False, max_width=None):
        face = font(size, bold)
        lines = content.split("\n")
        ascent, descent = (metric / SCALE for metric in face.getmetrics())
        line_height = size * 1.25
        baseline = y - (len(lines) - 1) * line_height / 2 + (ascent - descent) / 2
        for i, line in enumerate(lines):
            width = self.paint.textlength(line, font=face) / SCALE
            if max_width is not None:
                assert width <= max_width, (line, width, max_width)
            position = baseline + i * line_height
            assert x - width / 2 >= 0 and x + width / 2 <= self.width, line
            assert position - ascent >= 0 and position + descent <= self.height, line
            ET.SubElement(self.svg, tag("text"), {
                "x": str(x), "y": str(position), "text-anchor": "middle",
                "font-family": "Arial, Helvetica, sans-serif", "font-size": str(size),
                "font-weight": "700" if bold else "400", "fill": INK}).text = line
            self.paint.text((x * SCALE, position * SCALE), line, font=face, fill=INK, anchor="ms")

    def box(self, x, y, width, height, content, size=28, fill="white", bold=False):
        self.rect(x, y, width, height, fill=fill)
        self.text(x + width / 2, y + height / 2, content, size, bold, max_width=width - 24)

    def polygon(self, points, fill="white", line=2):
        ET.SubElement(self.svg, tag("polygon"), {
            "points": " ".join(f"{x},{y}" for x, y in points), "fill": fill,
            "stroke": INK, "stroke-width": str(line), "stroke-linejoin": "round"})
        scaled = [(round(x * SCALE), round(y * SCALE)) for x, y in points]
        self.paint.polygon(scaled, fill=fill)
        self.paint.line(scaled + [scaled[0]], fill=INK, width=round(line * SCALE), joint="curve")

    def arrow(self, points, start=False, end=True):
        ET.SubElement(self.svg, tag("polyline"), {
            "points": " ".join(f"{x},{y}" for x, y in points), "fill": "none",
            "stroke": INK, "stroke-width": "2.5", "stroke-linejoin": "round"})
        self.paint.line([(round(x * SCALE), round(y * SCALE)) for x, y in points],
                        fill=INK, width=5, joint="curve")
        for active, tip, previous in ((start, points[0], points[1]), (end, points[-1], points[-2])):
            if not active:
                continue
            angle = math.atan2(tip[1] - previous[1], tip[0] - previous[0])
            base = (tip[0] - 12 * math.cos(angle), tip[1] - 12 * math.sin(angle))
            perpendicular = (-5 * math.sin(angle), 5 * math.cos(angle))
            self.polygon([tip, (base[0] + perpendicular[0], base[1] + perpendicular[1]),
                          (base[0] - perpendicular[0], base[1] - perpendicular[1])], fill=INK, line=1)

    def save(self, name):
        ET.indent(self.svg)
        ET.ElementTree(self.svg).write(HERE / f"{name}.svg", encoding="utf-8", xml_declaration=True)
        self.image.save(HERE / f"{name}.png", dpi=(300, 300), optimize=True)
        print(f"{name}: SVG 160 mm; PNG {self.image.width} x {self.image.height}, 300 dpi")


def architecture():
    drawing = Drawing(1200, 800, "Visão geral da arquitetura do chatbot",
        "WhatsApp por Evolution ou Twilio interage com um backend Python. Conversa e menus, "
        "núcleo RAG e índice FAISS local pertencem ao mesmo processo. Documentos e embeddings "
        "alimentam o índice. O banco relacional registra estado e histórico; a Groq é o serviço externo de geração.")
    drawing.rect(330, 25, 490, 750, fill="#f5f5f5", stroke="#707070", radius=16)
    drawing.text(575, 85, "Backend Python\napi/ e app/ no mesmo processo", size=27, bold=True, max_width=460)
    drawing.box(20, 175, 245, 110, "WhatsApp\nEvolution ou Twilio", size=25)
    drawing.box(380, 170, 390, 120, "Conversa e menus\napi/", bold=True)
    drawing.box(380, 400, 390, 120, "Núcleo RAG\napp/", bold=True)
    drawing.box(405, 650, 340, 95, "Índice FAISS\nlocal, em memória", size=27)
    drawing.box(20, 610, 245, 110, "Documentos TXT\ne modelos locais", size=25)
    drawing.box(900, 170, 280, 120, "Banco relacional\nEstado e registros", size=26)
    drawing.box(900, 400, 280, 120, "Groq\nGeração externa", size=28)
    drawing.arrow([(265, 230), (380, 230)], start=True)
    drawing.arrow([(770, 230), (900, 230)], start=True)
    drawing.text(835, 180, "leitura /\ngravação", size=20, max_width=120)
    drawing.arrow([(575, 290), (575, 400)], start=True)
    drawing.text(675, 345, "consulta\ndocumental", size=22, max_width=170)
    drawing.arrow([(770, 460), (900, 460)], start=True)
    drawing.text(835, 435, "inferência", size=20, max_width=120)
    drawing.arrow([(575, 520), (575, 650)], start=True)
    drawing.text(670, 585, "busca local", size=23, max_width=170)
    drawing.arrow([(265, 665), (405, 665)])
    drawing.text(335, 630, "gera índice", size=19, max_width=145)
    drawing.save("visao-geral")


def hybrid_flow():
    drawing = Drawing(1200, 1320, "Fluxo híbrido de menu e consulta documental",
        "O ChatService trata comandos, onboarding e estado da conversa. Respostas locais e "
        "navegação não usam o RAG. Uma opção de menu com consulta usa a pergunta do JSON; "
        "texto livre usa a pergunta digitada. "
        "Os dois caminhos documentais recuperam contexto no FAISS e solicitam geração externa "
        "na Groq. O backend adapta o resultado, persiste e devolve ao adaptador do canal.")
    drawing.box(430, 25, 340, 90, "Mensagem recebida\nChatService", size=27)
    drawing.arrow([(600, 115), (600, 170)])
    drawing.polygon([(600, 170), (765, 255), (600, 340), (435, 255)], fill="#f0f0f0")
    drawing.text(600, 255, "Comando, estado\ne tipo de entrada", size=25, max_width=235)
    drawing.arrow([(435, 255), (190, 255), (190, 425)])
    drawing.text(310, 218, "Sem consulta ao RAG", size=23, max_width=240)
    drawing.arrow([(600, 340), (600, 425)])
    drawing.text(690, 380, "Menu com\nconsulta", size=23, max_width=150)
    drawing.arrow([(765, 255), (1010, 255), (1010, 425)])
    drawing.text(890, 218, "Texto livre", size=24, max_width=240)
    drawing.box(35, 425, 310, 110, "Comando, onboarding\nou resposta de menu", size=25)
    drawing.box(445, 425, 310, 110, "Pergunta\nconfigurada no JSON", size=25)
    drawing.box(855, 425, 310, 110, "Pergunta em\ntexto livre", size=27)
    drawing.arrow([(600, 535), (600, 585), (805, 585)], end=False)
    drawing.arrow([(1010, 535), (1010, 585), (805, 585)], end=False)
    drawing.arrow([(805, 585), (805, 635)])
    drawing.box(520, 635, 570, 110, "Recuperar trechos no FAISS\nMontar pergunta + contexto", size=28)
    drawing.arrow([(805, 745), (805, 825)])
    drawing.box(575, 825, 460, 95, "Gerar resposta\nGroq externa", size=28)
    drawing.arrow([(805, 920), (805, 1000)])
    drawing.box(540, 1000, 530, 95, "Adaptar resultado\nPersonalização ou resposta de ausência", size=25)
    drawing.arrow([(805, 1095), (805, 1145), (660, 1145), (660, 1190)])
    drawing.box(385, 1190, 550, 100, "Persistir resposta e auditoria\nDevolver ao adaptador", size=28)
    drawing.arrow([(190, 535), (190, 1240), (385, 1240)])
    drawing.text(330, 870, "Sem consulta\ndocumental", size=24, max_width=220)
    drawing.save("fluxo-hibrido")


if __name__ == "__main__":
    architecture()
    hybrid_flow()
