from PyQt6.QtWidgets import QApplication
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtGui import QImage, QPainter
from PyQt6.QtCore import Qt
from PIL import Image
from pathlib import Path
import sys

# Logotipo Aegis 3.0: Monograma Escudo Cinético Minimalista Flotante (Sin borde negro, sin caja)
AEGIS_KINETIC_RIBBON_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="100%" height="100%">
  <defs>
    <!-- Gradiente Cinta Principal Izquierda / Cresta (Cian Neón a Azul Eléctrico) -->
    <linearGradient id="primaryGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#00f5ff" />
      <stop offset="35%" stop-color="#00a8ff" />
      <stop offset="100%" stop-color="#0055ff" />
    </linearGradient>

    <!-- Gradiente Cinta Derecha (Azul Eléctrico a Índigo Violeta) -->
    <linearGradient id="secondaryGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#38bdf8" />
      <stop offset="50%" stop-color="#4f46e5" />
      <stop offset="100%" stop-color="#7c3aed" />
    </linearGradient>

    <!-- Gradiente del Puente / Núcleo Central -->
    <linearGradient id="bridgeGrad" x1="0%" y1="50%" x2="100%" y2="50%">
      <stop offset="0%" stop-color="#00f5ff" />
      <stop offset="100%" stop-color="#6366f1" />
    </linearGradient>

    <!-- Sombra de superposición para efecto de pliegue tridimensional suave -->
    <filter id="foldShadow" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="-4" dy="10" stdDeviation="12" flood-color="#020617" flood-opacity="0.45" />
    </filter>

    <!-- Resplandor sutil para dar volumen orgánico -->
    <filter id="subtleGlow" x="-15%" y="-15%" width="130%" height="130%">
      <feGaussianBlur stdDeviation="6" result="blur" />
      <feComposite in="SourceGraphic" in2="blur" operator="over" />
    </filter>
  </defs>

  <g id="aegis-glyph">
    <!-- 1. Ala Derecha / Lazo Trasero (Fluye desde la cúspide hacia la pierna derecha) -->
    <path d="M 256, 72
             C 278, 72 296, 86 308, 106
             L 404, 282
             C 426, 322 418, 372 384, 404
             C 362, 424 330, 428 304, 412
             C 282, 398 274, 372 284, 348
             L 336, 248
             L 256, 178
             Z"
          fill="url(#secondaryGrad)" />

    <!-- 2. Ala Izquierda Principal / Escudo Frontal (Fluye desde la base izquierda hacia la cima y pliega en el centro) -->
    <path d="M 128, 404
             C 94, 372 86, 322 108, 282
             L 204, 106
             C 216, 86 234, 72 256, 72
             C 278, 72 296, 86 308, 106
             L 348, 180
             C 358, 198 352, 222 334, 232
             C 316, 242 292, 236 282, 218
             L 256, 170
             L 176, 318
             C 166, 336 172, 360 190, 370
             C 208, 380 232, 374 242, 356
             L 256, 330
             L 256, 400
             C 246, 414 228, 426 208, 426
             C 174, 426 146, 418 128, 404 Z"
          fill="url(#primaryGrad)"
          filter="url(#foldShadow)" />

    <!-- 3. Puente Transversal Orgánico (Forma la barra de la 'A' y cierra el perfil de escudo) -->
    <path d="M 166, 292
             C 166, 276 180, 264 196, 264
             L 316, 264
             C 332, 264 346, 276 346, 292
             C 346, 308 332, 320 316, 320
             L 196, 320
             C 180, 320 166, 308 166, 292 Z"
          fill="url(#bridgeGrad)"
          filter="url(#foldShadow)" />

    <!-- 4. Núcleo Lumínico Central (Cresta de protección / Enfoque minimalista) -->
    <circle cx="256" cy="188" r="14" fill="#ffffff" opacity="0.95" filter="url(#subtleGlow)" />
  </g>
</svg>
"""

# Guardar nuevo SVG
svg_path = Path("src/ui/assets/aegis-logo.svg")
svg_path.write_text(AEGIS_KINETIC_RIBBON_SVG, encoding="utf-8")
print(f"[OK] SVG limpio guardado en: {svg_path.resolve()}")

# Renderizar a PNG de alta resolución con transparencia
app = QApplication(sys.argv)
renderer = QSvgRenderer(str(svg_path))
image = QImage(512, 512, QImage.Format.Format_ARGB32)
image.fill(Qt.GlobalColor.transparent)

painter = QPainter(image)
painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
renderer.render(painter)
painter.end()

png_path = Path("src/ui/assets/aegis-logo-512.png")
image.save(str(png_path), "PNG")
print(f"[OK] PNG 512x512 guardado en: {png_path.resolve()}")

# Copiar a artifacts
dst_artifact = Path(r"C:\Users\PC\.gemini\antigravity\brain\d4058586-4a10-4ced-9ee7-6e7cabb89661\aegis-logo-512.png")
import shutil
shutil.copy2(png_path, dst_artifact)
print(f"[OK] Copiado a artifacts: {dst_artifact.exists()}")

# Guardar icono .ico
pil_img = Image.open(str(png_path))
ico_path = Path("src/ui/assets/aegis.ico")
pil_img.save(str(ico_path), format="ICO", sizes=[(16,16), (24,24), (32,32), (48,48), (64,64), (128,128), (256,256)])
print(f"[OK] ICO actualizado en: {ico_path.resolve()}")
