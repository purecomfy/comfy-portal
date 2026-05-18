# ComfyUI Linux Install Agent Guide

Этот файл предназначен для агента, который работает на Linux-машине пользователя и должен полностью поставить ComfyUI, зависимости, ноды, модели и туннель. Не считай это обычной инструкцией для чтения: выполняй шаги, проверяй результат после каждого этапа и в конце выдай пользователю короткий отчет.

Цель: получить рабочий ComfyUI на `0.0.0.0:8188`, установить набор нод и моделей из Comfy Portal, проверить API ComfyUI, затем помочь поднять публичную ссылку через LocalTunnel и при желании создать one-click запускатор.


## Правила Работы Агента

- Не удаляй существующую установку ComfyUI без явного разрешения.
- Если ComfyUI уже установлен, сначала определи путь и проверь, можно ли доустановить недостающее.
- Не считай установку успешной, пока `http://127.0.0.1:8188/system_stats` и `http://127.0.0.1:8188/queue` не отвечают JSON.
- Не считай публичный туннель успешным по факту открытия HTML-страницы. Проверяй именно `PUBLIC_URL/system_stats`.
- Если скачивание модели не удалось, не останавливай всю установку. Запиши модель в список ручной установки и продолжай.
- Для Civitai сначала используй встроенные ключи ниже. Если ключи удалены, невалидны или Civitai возвращает HTML/401/403/пустой файл, выведи ссылку и точную папку для ручного скачивания.
- В конце всегда выведи отчет: что установлено, что не установлено, где лежит ComfyUI, как запускать, какая публичная ссылка работает.

## Встроенные Переменные

Рекомендуемый путь установки:

```bash
export COMFY_BASE="${COMFY_BASE:-$HOME/Comfy}"
export COMFY_DIR="$COMFY_BASE/ComfyUI"
export VENV_DIR="$COMFY_BASE/venv"
export COMFY_PORT="${COMFY_PORT:-8188}"
```

Civitai ключи из Comfy Portal. Они нужны для автоматической загрузки Civitai/civitai.red моделей.

```bash
CIVITAI_KEYS=(
  "56400144e19ddacd31f7053d16d329cc"
  "bbbb9ffec2ac7eef075e1951c5c304ab"
)
```

## Этап 1. Диагностика Системы

Собери факты и покажи пользователю короткий вывод:

```bash
set -u

echo "== OS =="
cat /etc/os-release 2>/dev/null || true
uname -a

echo "== CPU/RAM/DISK =="
lscpu 2>/dev/null | sed -n '1,20p' || true
free -h || true
df -h "$HOME" || true

echo "== GPU =="
command -v nvidia-smi >/dev/null 2>&1 && nvidia-smi || true
lspci 2>/dev/null | grep -Ei 'vga|3d|display|nvidia|amd|intel' || true

echo "== Tools =="
for bin in python3 git curl wget aria2c ffmpeg node npm npx; do
  printf "%-10s" "$bin"
  command -v "$bin" || true
done

echo "== Network =="
curl -I --max-time 12 https://github.com >/dev/null && echo "GitHub OK" || echo "GitHub FAIL"
curl -I --max-time 12 https://huggingface.co >/dev/null && echo "HuggingFace OK" || echo "HuggingFace FAIL"
curl -I --max-time 12 https://civitai.com >/dev/null && echo "Civitai OK" || echo "Civitai FAIL"

echo "== Port 8188 =="
ss -ltnp 2>/dev/null | grep ":${COMFY_PORT} " || true
```

Оценка пригодности:

- NVIDIA GPU с нормальным `nvidia-smi`: ставь CUDA PyTorch.
- Нет NVIDIA GPU: ставь CPU PyTorch и предупреди, что генерация будет медленной.
- RAM меньше 16 GB: предупреди о риске OOM.
- Свободно меньше 60 GB: предупреди, что все модели могут не поместиться.
- Python ниже 3.10 или выше неподдерживаемой версии: установи подходящий Python или создай venv на доступной версии 3.10-3.12.

## Этап 2. Системные Зависимости

Определи пакетный менеджер и установи базовые пакеты.

### Debian/Ubuntu

```bash
sudo apt update
sudo apt install -y \
  git curl wget aria2 ffmpeg \
  python3 python3-venv python3-pip \
  build-essential pkg-config \
  libgl1 libglib2.0-0 libsm6 libxext6 libxrender1 \
  nodejs npm
```

### Fedora

```bash
sudo dnf install -y \
  git curl wget aria2 ffmpeg \
  python3 python3-pip \
  gcc gcc-c++ make pkgconf-pkg-config \
  mesa-libGL glib2 \
  nodejs npm
```

### Arch

```bash
sudo pacman -Syu --needed \
  git curl wget aria2 ffmpeg \
  python python-pip \
  base-devel pkgconf \
  nodejs npm
```

Если пакетный менеджер неизвестен, не угадывай. Выведи список нужных пакетов: `git`, `curl`, `wget`, `aria2`, `ffmpeg`, `python3`, `python3-venv`, `python3-pip`, build tools, OpenGL libs, `nodejs`, `npm`.

## Этап 3. Установка ComfyUI

Если `COMFY_DIR` уже существует, не клонируй заново. Выполни `git status`, `git remote -v`, проверь `main.py`.

```bash
mkdir -p "$COMFY_BASE"

if [ ! -d "$COMFY_DIR/.git" ]; then
  git clone https://github.com/comfyanonymous/ComfyUI.git "$COMFY_DIR"
else
  git -C "$COMFY_DIR" pull --ff-only || true
fi

python3 -m venv "$VENV_DIR"
. "$VENV_DIR/bin/activate"
python -m pip install --upgrade pip setuptools wheel
```

## Этап 4. PyTorch

Выбери режим:

```bash
if command -v nvidia-smi >/dev/null 2>&1 && nvidia-smi >/dev/null 2>&1; then
  export COMFY_DEVICE_MODE="cuda"
else
  export COMFY_DEVICE_MODE="cpu"
fi
echo "Selected mode: $COMFY_DEVICE_MODE"
```

Для CUDA сначала попробуй актуальный стабильный wheel. Если команда ниже не работает на конкретной машине, открой официальный selector PyTorch и выбери Linux + pip + Python + CUDA:

https://pytorch.org/get-started/locally/

```bash
if [ "$COMFY_DEVICE_MODE" = "cuda" ]; then
  python -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
else
  python -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
fi
```

Проверь:

```bash
python - <<'PY'
import torch
print("torch:", torch.__version__)
print("cuda_available:", torch.cuda.is_available())
if torch.cuda.is_available():
    print("cuda:", torch.version.cuda)
    print("gpu:", torch.cuda.get_device_name(0))
PY
```

Поставь зависимости ComfyUI:

```bash
cd "$COMFY_DIR"
python -m pip install -r requirements.txt
```

## Этап 5. ComfyUI Manager

```bash
mkdir -p "$COMFY_DIR/custom_nodes"
cd "$COMFY_DIR/custom_nodes"

if [ ! -d "ComfyUI-Manager/.git" ]; then
  git clone https://github.com/ltdrdata/ComfyUI-Manager.git
else
  git -C ComfyUI-Manager pull --ff-only || true
fi

if [ -f "ComfyUI-Manager/requirements.txt" ]; then
  "$VENV_DIR/bin/python" -m pip install -r "ComfyUI-Manager/requirements.txt" || true
fi
```

## Этап 6. Custom Nodes

Установи все ноды в `ComfyUI/custom_nodes`. Если папка уже существует, обнови через `git pull --ff-only`. Если `requirements.txt` есть, ставь зависимости через venv ComfyUI.

```bash
CUSTOM_NODES=(
  "ComfyUI Impact Pack|ComfyUI-Impact-Pack|https://github.com/ltdrdata/ComfyUI-Impact-Pack.git"
  "ComfyUI-Custom-Scripts|ComfyUI-Custom-Scripts|https://github.com/pythongosssss/ComfyUI-Custom-Scripts.git"
  "rgthree-comfy|rgthree-comfy|https://github.com/rgthree/rgthree-comfy.git"
  "ComfyUI-Easy-Use|ComfyUI-Easy-Use|https://github.com/yolain/ComfyUI-Easy-Use.git"
  "ComfyUI_UltimateSDUpscale|ComfyUI_UltimateSDUpscale|https://github.com/ssitu/ComfyUI_UltimateSDUpscale.git"
  "ComfyUI Impact Subpack|ComfyUI-Impact-Subpack|https://github.com/ltdrdata/ComfyUI-Impact-Subpack.git"
  "ComfyUI_Swwan|ComfyUI_Swwan|https://github.com/aining2022/ComfyUI_Swwan.git"
  "CG Use Everywhere|cg-use-everywhere|https://github.com/chrisgoringe/cg-use-everywhere.git"
  "Save Image with Generation Metadata|ImageWithMetadata|https://github.com/shin131002/ComfyUI-ImageWithMetadata.git"
  "Various ComfyUI Nodes by Type|comfyui-various|https://github.com/jamesWalker55/comfyui-various.git"
  "CRT-Nodes|CRT-Nodes|https://github.com/PGCRT/CRT-Nodes.git"
  "ComfyUI-Chibi-Nodes|ComfyUI-Chibi-Nodes|https://github.com/chibiace/ComfyUI-Chibi-Nodes.git"
  "ComfyUI_essentials|ComfyUI_essentials|https://github.com/cubiq/ComfyUI_essentials.git"
  "Comfyroll Studio|ComfyUI_Comfyroll_CustomNodes|https://github.com/Suzie1/ComfyUI_Comfyroll_CustomNodes.git"
  "ComfyUI ControlNet Aux|comfyui_controlnet_aux|https://github.com/Fannovel16/comfyui_controlnet_aux.git"
  "ComfyUI LayerStyle|ComfyUI_LayerStyle|https://github.com/chflame163/ComfyUI_LayerStyle.git"
  "ComfyUI-KJNodes|ComfyUI-KJNodes|https://github.com/kijai/ComfyUI-KJNodes.git"
  "ComfyUI-SeedVR2 VideoUpscaler|ComfyUI-SeedVR2_VideoUpscaler|https://github.com/numz/ComfyUI-SeedVR2_VideoUpscaler.git"
  "ComfyUI-RMBG|ComfyUI-RMBG|https://github.com/1038lab/ComfyUI-RMBG.git"
  "ComfyUI-Crystools|ComfyUI-Crystools|https://github.com/crystian/ComfyUI-Crystools.git"
  "ComfyUI-Florence2|ComfyUI-Florence2|https://github.com/kijai/ComfyUI-Florence2.git"
  "ComfyUI-ReActor|ComfyUI-ReActor|https://github.com/Gourieff/ComfyUI-ReActor.git"
  "ComfyUI-QwenVL|ComfyUI-QwenVL|https://github.com/1038lab/ComfyUI-QwenVL.git"
  "ComfyUI_Fill-Nodes|ComfyUI_Fill-Nodes|https://github.com/filliptm/ComfyUI_Fill-Nodes.git"
  "Derfuu ComfyUI ModdedNodes|Derfuu_ComfyUI_ModdedNodes|https://github.com/Derfuu/Derfuu_ComfyUI_ModdedNodes.git"
  "facerestore_cf|facerestore_cf|https://github.com/mav-rik/facerestore_cf.git"
  "ComfyUI-mxToolkit|ComfyUI-mxToolkit|https://github.com/Smirnov75/ComfyUI-mxToolkit.git"
  "ComfyUI post processing nodes|ComfyUI-post-processing-nodes|https://github.com/EllangoK/ComfyUI-post-processing-nodes.git"
  "virtuoso-nodes|virtuoso-nodes|https://github.com/chrisfreilich/virtuoso-nodes.git"
  "ComfyUI QualityOfLifeSuit Omar92|ComfyUI-QualityOfLifeSuit_Omar92|https://github.com/omar92/ComfyUI-QualityOfLifeSuit_Omar92.git"
  "ComfyUI WD14 Tagger|ComfyUI-WD14-Tagger|https://github.com/pythongosssss/ComfyUI-WD14-Tagger.git"
  "ComfyUI Advanced ControlNet|ComfyUI-Advanced-ControlNet|https://github.com/Kosinkadink/ComfyUI-Advanced-ControlNet.git"
  "ComfyUI tinyterraNodes|ComfyUI_tinyterraNodes|https://github.com/TinyTerra/ComfyUI_tinyterraNodes.git"
  "ComfyUI DepthAnythingV2|ComfyUI-DepthAnythingV2|https://github.com/kijai/ComfyUI-DepthAnythingV2.git"
  "ComfyUI Mira|ComfyUI_Mira|https://github.com/mirabarukaso/ComfyUI_Mira.git"
  "Comfy Image Saver|comfy-image-saver|https://github.com/giriss/comfy-image-saver.git"
  "ComfyUI-GGUF|ComfyUI-GGUF|https://github.com/city96/ComfyUI-GGUF.git"
)

mkdir -p "$COMFY_DIR/custom_nodes"
NODE_OK=()
NODE_FAIL=()

for item in "${CUSTOM_NODES[@]}"; do
  IFS='|' read -r title folder repo <<< "$item"
  target="$COMFY_DIR/custom_nodes/$folder"
  node_failed=0
  echo "== Node: $title =="
  if [ -d "$target/.git" ]; then
    git -C "$target" pull --ff-only || { NODE_FAIL+=("$title: git pull failed"); node_failed=1; }
  elif [ -d "$target" ]; then
    echo "Folder exists but is not a git repo: $target"
    NODE_OK+=("$title: folder exists")
    continue
  else
    git clone --depth 1 "$repo" "$target" || { NODE_FAIL+=("$title: clone failed"); continue; }
  fi

  if [ -f "$target/requirements.txt" ]; then
    "$VENV_DIR/bin/python" -m pip install -r "$target/requirements.txt" || { NODE_FAIL+=("$title: requirements failed"); node_failed=1; }
  fi

  [ "$node_failed" -eq 0 ] && [ -d "$target" ] && NODE_OK+=("$title")
done
```

## Этап 7. Модели

Создай папки и скачай модели. Для больших файлов лучше использовать `aria2c`; если его нет, используй `wget -c` или `curl -L`.

Правила:

- Если файл уже есть и размер больше 1 MB, пропусти.
- Для HuggingFace обычно достаточно прямой ссылки.
- Для Civitai/civitai.red пробуй ключи из `CIVITAI_KEYS`.
- Если все ключи не сработали, дай пользователю ручную инструкцию.
- Если файл скачался как HTML, JSON с ошибкой или очень маленький файл, считай скачивание неудачным.

```bash
echo "== Model choice =="
echo "mopMixtureOfPerverts v20, xxxRay DMD2 - слабые: выбирай для слабой GPU или если нужно меньше места."
echo "Nova Anime XL IL v170 - средняя: хороший вариант по умолчанию."
echo "Intorealism ZIT v40, RedCraft ErnieRedmix - тяжелые: выбирай только если хватает места и VRAM."
echo "Оставь пусто для рекомендации: mopofmixture,xxray,novaanime."
read -r -p "Какие модели скачать? [mopofmixture,xxray,novaanime]: " MODEL_SELECTION
MODEL_SELECTION="${MODEL_SELECTION:-mopofmixture,xxray,novaanime}"
MODEL_SELECTION="$(printf '%s' "$MODEL_SELECTION" | tr '[:upper:]' '[:lower:]' | tr -d ' ')"

model_selected() {
  group="$1"
  [ "$group" = "always" ] && return 0
  case ",$MODEL_SELECTION," in
    *",$group,"*) return 0 ;;
    *) return 1 ;;
  esac
}

MODELS=(
  "SAM|sam_vit_b_01ec64.pth|ComfyUI/models/sams|https://dl.fbaipublicfiles.com/segment_anything/sam_vit_b_01ec64.pth|always"
  "RealESRGAN x2|RealESRGAN_x2.pth|ComfyUI/models/upscale_models|https://huggingface.co/ai-forever/Real-ESRGAN/resolve/main/RealESRGAN_x2.pth?download=true|always"
  "Control LoRA Canny|control-lora-canny-rank256.safetensors|ComfyUI/models/controlnet|https://huggingface.co/stabilityai/control-lora/resolve/main/control-LoRAs-rank256/control-lora-canny-rank256.safetensors?download=true|always"
  "VAE|ae.safetensors|ComfyUI/models/vae|https://huggingface.co/Comfy-Org/HiDream-I1_ComfyUI/resolve/main/split_files/vae/ae.safetensors?download=true|always"
  "CLIP / text_encoders|qwen_3_4b.safetensors|ComfyUI/models/text_encoders|https://huggingface.co/Comfy-Org/z_image_turbo/resolve/main/split_files/text_encoders/qwen_3_4b.safetensors?download=true|always"
  "ControlNet Union|Z-Image-Turbo-Fun-Controlnet-Union-2.1-2602-8steps.safetensors|ComfyUI/models/model_patches|https://huggingface.co/alibaba-pai/Z-Image-Turbo-Fun-Controlnet-Union-2.1/resolve/main/Z-Image-Turbo-Fun-Controlnet-Union-2.1-2602-8steps.safetensors?download=true|always"
  "Embeddings|embedding_model.pt|ComfyUI/models/embeddings|https://civitai.com/api/download/models/2121199?type=Model&format=Other|always"
  "Upscale 4x_NMKD-Siax_200k|4x_NMKD-Siax_200k.pth|ComfyUI/models/upscale_models|https://huggingface.co/gemasai/4x_NMKD-Siax_200k/resolve/main/4x_NMKD-Siax_200k.pth?download=true|always"
  "mopMixtureOfPerverts v20|mopMixtureOfPerverts_v20.safetensors|ComfyUI/models/checkpoints|https://civitai.red/api/download/models/2159501?type=Model&format=SafeTensor&size=pruned&fp=fp16|mopofmixture"
  "xxxRay DMD2|xxxRay_dmd2.safetensors|ComfyUI/models/checkpoints|https://civitai.red/api/download/models/1624818?type=Model&format=SafeTensor&size=full&fp=fp16|xxray"
  "Nova Anime XL IL v170|novaAnimeXL_ilV170.safetensors|ComfyUI/models/checkpoints|https://civitai.red/api/download/models/2741698?type=Model&format=SafeTensor&size=pruned&fp=fp16|novaanime"
  "Intorealism ZIT v40|intorealism_zitV40.safetensors|ComfyUI/models/unet|https://civitai.red/api/download/models/2912231?type=Model&format=SafeTensor&size=full&fp=fp8|intorealism"
  "RedCraft ErnieRedmix UNet|redcraft_ernieRedmix.safetensors|ComfyUI/models/unet|https://civitai.red/api/download/models/2891710?type=Diffusion%20Model&format=Other&fp=fp8|redcraft"
  "RedCraft ErnieRedmix Text Encoder|redcraft_ernieRedmix_txt.safetensors|ComfyUI/models/text_encoders|https://civitai.red/api/download/models/2891710?fileId=2773413|redcraft"
  "Flux2 Tiny VAE|flux2-tiny-vae.safetensors|ComfyUI/models/vae|https://civitai.red/api/download/models/2891710?fileId=2773335|redcraft"
  "bbox/face_yolov8m.pt|face_yolov8m.pt|ComfyUI/models/ultralytics/bbox|https://huggingface.co/alexgenovese/ultralytics/resolve/main/bbox/face_yolov8m.pt?download=true|always"
  "bbox/Eyeful_v2-Paired.pt|Eyeful_v2-Paired.pt|ComfyUI/models/ultralytics/bbox|https://huggingface.co/MidnightRunner/Ultralytics/resolve/main/bbox/Eyeful_v2-Paired.pt?download=true|always"
  "bbox/hand_yolov9c.pt|hand_yolov9c.pt|ComfyUI/models/ultralytics/bbox|https://huggingface.co/Bingsu/adetailer/resolve/main/hand_yolov9c.pt?download=true|always"
)

download_model() {
  title="$1"
  filename="$2"
  rel_dir="$3"
  url="$4"
  target_dir="$COMFY_BASE/$rel_dir"
  target="$target_dir/$filename"
  mkdir -p "$target_dir"

  if [ -s "$target" ] && [ "$(stat -c%s "$target" 2>/dev/null || echo 0)" -gt 1048576 ]; then
    echo "Already exists: $target"
    return 0
  fi

  tmp="$target.part"
  rm -f "$tmp"

  is_valid_download() {
    [ -s "$tmp" ] || return 1
    [ "$(stat -c%s "$tmp" 2>/dev/null || echo 0)" -gt 1048576 ] || return 1
    ! head -c 256 "$tmp" | grep -Eqi '<html|<!doctype|captcha|unauthorized|forbidden'
  }

  mark_manual_download() {
    rm -f "$tmp"
    echo "MANUAL_DOWNLOAD_REQUIRED|$title|$url|$target_dir|$filename" >> "$COMFY_BASE/manual_downloads.txt"
    echo "Manual download required: $title"
    echo "URL: $url"
    echo "Put file here: $target"
  }

  try_download() {
    dl_url="$1"
    auth_header="$2"
    if command -v aria2c >/dev/null 2>&1; then
      if [ -n "$auth_header" ]; then
        aria2c -x 8 -s 8 -c --header="$auth_header" -o "$(basename "$tmp")" -d "$(dirname "$tmp")" "$dl_url"
      else
        aria2c -x 8 -s 8 -c -o "$(basename "$tmp")" -d "$(dirname "$tmp")" "$dl_url"
      fi
    else
      if [ -n "$auth_header" ]; then
        curl -L --fail --retry 3 -H "$auth_header" -o "$tmp" "$dl_url"
      else
        curl -L --fail --retry 3 -o "$tmp" "$dl_url"
      fi
    fi
  }

  is_civitai=0
  case "$url" in
    *civitai.com*|*civitai.red*) is_civitai=1 ;;
  esac

  downloaded_ok=0
  if [ "$is_civitai" -eq 1 ] && [ "${#CIVITAI_KEYS[@]}" -gt 0 ]; then
    for key in "${CIVITAI_KEYS[@]}"; do
      [ -z "$key" ] && continue
      rm -f "$tmp"
      echo "Downloading with Civitai key: $title"
      if try_download "$url" "Authorization: Bearer $key" && is_valid_download; then
        downloaded_ok=1
        break
      fi
      rm -f "$tmp"
    done
  else
    echo "Downloading: $title"
    rm -f "$tmp"
    if try_download "$url" "" && is_valid_download; then
      downloaded_ok=1
    fi
  fi

  if [ "$downloaded_ok" -ne 1 ]; then
    mark_manual_download
    return 1
  fi

  mv "$tmp" "$target"
  echo "OK: $target"
  return 0
}

rm -f "$COMFY_BASE/manual_downloads.txt"
MODEL_OK=()
MODEL_FAIL=()

for item in "${MODELS[@]}"; do
  IFS='|' read -r title filename rel_dir url model_group <<< "$item"
  if ! model_selected "${model_group:-always}"; then
    echo "Skipped by model choice: $title"
    continue
  fi
  if download_model "$title" "$filename" "$rel_dir" "$url"; then
    MODEL_OK+=("$title")
  else
    MODEL_FAIL+=("$title")
  fi
done
```

Если `manual_downloads.txt` появился, покажи его пользователю в понятном виде:

```bash
if [ -f "$COMFY_BASE/manual_downloads.txt" ]; then
  echo "== Manual model downloads required =="
  while IFS='|' read -r marker title url folder filename; do
    echo "- $title"
    echo "  URL: $url"
    echo "  Folder: $folder"
    echo "  Filename: $filename"
  done < "$COMFY_BASE/manual_downloads.txt"
fi
```

## Этап 8. Проверка Установки

Создай диагностический запуск ComfyUI:

```bash
mkdir -p "$COMFY_BASE/logs"

cd "$COMFY_DIR"
"$VENV_DIR/bin/python" main.py --listen 0.0.0.0 --port "$COMFY_PORT" > "$COMFY_BASE/logs/comfy.stdout.log" 2> "$COMFY_BASE/logs/comfy.stderr.log" &
COMFY_PID=$!
echo "$COMFY_PID" > "$COMFY_BASE/comfy.pid"

for i in $(seq 1 90); do
  if curl -fsS "http://127.0.0.1:$COMFY_PORT/system_stats" >/dev/null; then
    echo "ComfyUI API is ready"
    break
  fi
  sleep 1
done

if ! curl -fsS "http://127.0.0.1:$COMFY_PORT/system_stats" >/dev/null; then
  echo "ComfyUI did not become ready."
  tail -n 120 "$COMFY_BASE/logs/comfy.stderr.log" 2>/dev/null || true
  tail -n 120 "$COMFY_BASE/logs/comfy.stdout.log" 2>/dev/null || true
  exit 1
fi

curl -fsS "http://127.0.0.1:$COMFY_PORT/system_stats" | head -c 500 && echo
curl -fsS "http://127.0.0.1:$COMFY_PORT/queue" && echo
```

Если API не отвечает:

- покажи последние 120 строк `logs/comfy.stderr.log`
- покажи последние 120 строк `logs/comfy.stdout.log`
- проверь порт `ss -ltnp | grep 8188`
- проверь `python -c "import torch; print(torch.cuda.is_available())"`

## Этап 9. Проверка Установленных Компонентов

Сверь ноды:

```bash
echo "== Node check =="
for item in "${CUSTOM_NODES[@]}"; do
  IFS='|' read -r title folder repo <<< "$item"
  if [ -d "$COMFY_DIR/custom_nodes/$folder" ]; then
    echo "OK   $title"
  else
    echo "MISS $title"
  fi
done
```

Сверь модели:

```bash
echo "== Model check =="
for item in "${MODELS[@]}"; do
  IFS='|' read -r title filename rel_dir url <<< "$item"
  target="$COMFY_BASE/$rel_dir/$filename"
  if [ -s "$target" ]; then
    echo "OK   $title -> $target"
  else
    echo "MISS $title -> $target"
  fi
done
```

## Этап 10. Туннель LocalTunnel

LocalTunnel дает ссылку `loca.lt`. Можно указать свой subdomain, но он может быть занят или вести не туда. Всегда проверяй `PUBLIC_URL/system_stats`.

Установка:

```bash
sudo npm install -g localtunnel
```

Запуск со случайной ссылкой:

```bash
lt --port "$COMFY_PORT" --local-host 127.0.0.1
```

Запуск со своим именем:

```bash
SUBDOMAIN="${SUBDOMAIN:-comfylocal$((1000 + RANDOM % 9000))}"
lt --port "$COMFY_PORT" --local-host 127.0.0.1 --subdomain "$SUBDOMAIN"
```

Проверка:

```bash
PUBLIC_URL="https://example.loca.lt"
curl -fsS "$PUBLIC_URL/system_stats" | head -c 500 && echo
```

Если открывается чужая HTML-страница, это не рабочий туннель. Смени subdomain или используй случайную ссылку.

## Этап 11. One-click Скрипты

Предложи пользователю создать один из вариантов.

### start_comfy_localtunnel.sh

```bash
cat > "$COMFY_BASE/start_comfy_localtunnel.sh" <<'SH'
#!/usr/bin/env bash
set -euo pipefail

COMFY_BASE="${COMFY_BASE:-$HOME/Comfy}"
COMFY_DIR="$COMFY_BASE/ComfyUI"
VENV_DIR="$COMFY_BASE/venv"
COMFY_PORT="${COMFY_PORT:-8188}"
SUBDOMAIN="${SUBDOMAIN:-}"
mkdir -p "$COMFY_BASE/logs"

if ! curl -fsS "http://127.0.0.1:$COMFY_PORT/system_stats" >/dev/null 2>&1; then
  cd "$COMFY_DIR"
  "$VENV_DIR/bin/python" main.py --listen 0.0.0.0 --port "$COMFY_PORT" > "$COMFY_BASE/logs/comfy.stdout.log" 2> "$COMFY_BASE/logs/comfy.stderr.log" &
  echo $! > "$COMFY_BASE/comfy.pid"
fi

for i in $(seq 1 90); do
  curl -fsS "http://127.0.0.1:$COMFY_PORT/system_stats" >/dev/null 2>&1 && break
  sleep 1
done

if ! curl -fsS "http://127.0.0.1:$COMFY_PORT/system_stats" >/dev/null 2>&1; then
  echo "ComfyUI did not become ready."
  tail -n 120 "$COMFY_BASE/logs/comfy.stderr.log" 2>/dev/null || true
  tail -n 120 "$COMFY_BASE/logs/comfy.stdout.log" 2>/dev/null || true
  exit 1
fi

if [ -n "$SUBDOMAIN" ]; then
  lt --port "$COMFY_PORT" --local-host 127.0.0.1 --subdomain "$SUBDOMAIN" 2>&1 | tee "$COMFY_BASE/logs/localtunnel.log"
else
  lt --port "$COMFY_PORT" --local-host 127.0.0.1 2>&1 | tee "$COMFY_BASE/logs/localtunnel.log"
fi
SH

chmod +x "$COMFY_BASE/start_comfy_localtunnel.sh"
echo "Created: $COMFY_BASE/start_comfy_localtunnel.sh"
```

### stop_comfy.sh

```bash
cat > "$COMFY_BASE/stop_comfy.sh" <<'SH'
#!/usr/bin/env bash
set -euo pipefail

COMFY_BASE="${COMFY_BASE:-$HOME/Comfy}"
if [ -f "$COMFY_BASE/comfy.pid" ]; then
  kill "$(cat "$COMFY_BASE/comfy.pid")" 2>/dev/null || true
  rm -f "$COMFY_BASE/comfy.pid"
fi
pkill -f "ComfyUI/main.py" 2>/dev/null || true
pkill -f "localtunnel" 2>/dev/null || true
echo "Stopped ComfyUI and tunnels."
SH

chmod +x "$COMFY_BASE/stop_comfy.sh"
echo "Created: $COMFY_BASE/stop_comfy.sh"
```

## Этап 12. Итоговый Отчет

В конце выведи:

```bash
echo "== Final report =="
echo "Comfy base: $COMFY_BASE"
echo "Comfy dir:  $COMFY_DIR"
echo "Venv:       $VENV_DIR"
echo "Port:       $COMFY_PORT"
echo "Mode:       ${COMFY_DEVICE_MODE:-unknown}"
echo
echo "Local URL:  http://127.0.0.1:$COMFY_PORT"
echo
echo "Scripts:"
ls -1 "$COMFY_BASE"/start_comfy_*.sh "$COMFY_BASE"/stop_comfy.sh 2>/dev/null || true
echo
echo "Manual downloads:"
if [ -f "$COMFY_BASE/manual_downloads.txt" ]; then
  cat "$COMFY_BASE/manual_downloads.txt"
else
  echo "none"
fi
```

Скажи пользователю:

- Для LocalTunnel: запускать `~/Comfy/start_comfy_localtunnel.sh`.
- Для остановки: запускать `~/Comfy/stop_comfy.sh`.
- Если нужен свой адрес, используй LocalTunnel subdomain и обязательно проверяй `PUBLIC_URL/system_stats`.
