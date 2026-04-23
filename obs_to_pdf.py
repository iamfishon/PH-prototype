import re
import base64
import pathlib
import markdown
import sys

def img_to_base64(img_path: pathlib.Path) -> str:
    ext = img_path.suffix.lower().lstrip(".")
    mime = {"jpg": "jpeg", "jpeg": "jpeg", "png": "png", "gif": "gif", "webp": "webp"}.get(ext, "png")
    data = base64.b64encode(img_path.read_bytes()).decode()
    return f"data:image/{mime};base64,{data}"

def convert(md_path: str, out_html: str):
    md_file = pathlib.Path(md_path)
    asset_dir = md_file.parent / "assets"
    text = md_file.read_text(encoding="utf-8")

    # 1. Obsidian ![[file|size]] → <img>
    def replace_obsidian_img(m):
        filename = m.group(1).strip()
        size = m.group(2)
        img_file = md_file.parent / filename
        if not img_file.exists():
            img_file = asset_dir / filename
        if img_file.exists():
            src = img_to_base64(img_file)
            width_attr = f' width="{size}"' if size else ""
            return f'<img src="{src}"{width_attr} style="max-width:100%;">'
        return m.group(0)
    text = re.sub(r'!\[\[([^\]|]+)(?:\|(\d+))?\]\]', replace_obsidian_img, text)

    # 2. Standard markdown images → direct <img> tag (avoid base64 inside markdown parser)
    def replace_std_img(m):
        alt, src = m.group(1), m.group(2)
        # strip obsidian size hint from alt e.g. "sign-sud1\|133" or "banner|200"
        size_match = re.search(r'\\?\|(\d+)$', alt)
        width_attr = f' width="{size_match.group(1)}"' if size_match else ""
        img_file = md_file.parent / src
        if not img_file.exists():
            img_file = asset_dir / pathlib.Path(src).name
        if img_file.exists():
            b64 = img_to_base64(img_file)
            return f'<img src="{b64}"{width_attr} style="max-width:100%;height:auto;">'
        return m.group(0)
    text = re.sub(r'!\[([^\]]*)\]\((?!data:)(assets/[^)]+|[^)]+\.(?:png|jpg|jpeg|gif|webp))\)', replace_std_img, text)

    # 3. ==highlight== → <mark>
    text = re.sub(r'==(.+?)==', r'<mark>\1</mark>', text)

    # 4. Convert markdown → HTML
    body = markdown.markdown(
        text,
        extensions=["tables", "fenced_code", "nl2br", "toc", "attr_list"]
    )

    html = f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="UTF-8">
<style>
  body {{ font-family: "Noto Sans TC", "Microsoft JhengHei", sans-serif; font-size: 13px; line-height: 1.6; margin: 20mm 18mm; color: #222; }}
  h1 {{ font-size: 20px; border-bottom: 2px solid #444; padding-bottom: 6px; }}
  h2 {{ font-size: 16px; border-bottom: 1px solid #ccc; padding-bottom: 4px; margin-top: 28px; }}
  h3, h4, h5 {{ font-size: 14px; margin-top: 16px; }}
  table {{ border-collapse: collapse; width: 100%; margin: 10px 0; font-size: 12px; page-break-inside: avoid; }}
  th, td {{ border: 1px solid #bbb; padding: 5px 8px; vertical-align: middle; word-break: break-word; }}
  th {{ background: #f0f0f0; font-weight: bold; }}
  img {{ max-width: 100%; height: auto; display: block; margin: 4px auto; }}
  mark {{ background: #ffe066; padding: 1px 2px; border-radius: 2px; }}
  code {{ background: #f5f5f5; padding: 1px 4px; border-radius: 3px; font-size: 11px; }}
  blockquote {{ border-left: 3px solid #aaa; margin: 0; padding-left: 12px; color: #555; }}
  hr {{ border: none; border-top: 1px solid #ddd; margin: 20px 0; }}
  h2, h3, h4 {{ page-break-after: avoid; }}
  ul, ol {{ page-break-inside: avoid; }}
  li {{ page-break-inside: avoid; }}
  @media print {{ body {{ margin: 0; }} }}
</style>
</head>
<body>
{body}
</body>
</html>"""

    pathlib.Path(out_html).write_text(html, encoding="utf-8")
    print(f"HTML saved: {out_html}")

if __name__ == "__main__":
    md = sys.argv[1]
    out = sys.argv[2]
    convert(md, out)
