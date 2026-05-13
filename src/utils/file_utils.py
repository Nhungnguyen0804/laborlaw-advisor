import json
from pathlib import Path
def load_json(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return None
    
def save_json(data, output_path, indent=2):
    output_path = Path(output_path)
    # tao folder neu chua co 
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=indent)
    
    print(f"Lưu tại {output_path}")


def save_txt(lines, output_path, mode="w"):
    output_path = Path(output_path)

    # tạo folder nếu chưa có
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, mode, encoding="utf-8") as f:
        if isinstance(lines, list):
            f.writelines(lines)
        else:
            f.write(lines)

    print(f"Lưu tại {output_path}")