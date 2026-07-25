import os
from PIL import Image, ImageOps

def get_target_dims(filename, relative_path):
    fn = filename.lower()
    if 'logo' in fn:
        return (400, 400)
    elif fn in ('chef.jpg', 'restaurant.avif', 'restaurant.jpg'):
        return (1200, 1200)
    else:
        return (800, 800)

def optimize_file(filepath, relative_path):
    orig_size_bytes = os.path.getsize(filepath)
    orig_size_kb = orig_size_bytes / 1024.0

    try:
        with Image.open(filepath) as img:
            orig_w, orig_h = img.size
            orig_fmt = img.format or 'JPEG'

            # Auto-rotate EXIF
            try:
                img = ImageOps.exif_transpose(img)
            except Exception:
                pass

            target_w, target_h = get_target_dims(os.path.basename(filepath), relative_path)
            
            # Resize if larger than target
            if orig_w > target_w or orig_h > target_h:
                img.thumbnail((target_w, target_h), Image.Resampling.LANCZOS)

            new_w, new_h = img.size

            # Save in place with quality=82, optimize=True, strip EXIF metadata
            ext = os.path.splitext(filepath)[1].lower()
            if ext in ('.jpg', '.jpeg'):
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                img.save(filepath, format='JPEG', quality=82, optimize=True)
            elif ext == '.png':
                if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                    img.save(filepath, format='PNG', optimize=True)
                else:
                    img = img.convert('RGB')
                    img.save(filepath, format='JPEG', quality=82, optimize=True)
            elif ext in ('.webp', '.avif'):
                fmt = 'WEBP' if ext == '.webp' else 'AVIF'
                try:
                    img.save(filepath, format=fmt, quality=82)
                except Exception:
                    # Fallback to WebP/JPEG if AVIF writer missing
                    if img.mode != 'RGB':
                        img = img.convert('RGB')
                    img.save(filepath, format='JPEG', quality=82, optimize=True)

        new_size_bytes = os.path.getsize(filepath)
        new_size_kb = new_size_bytes / 1024.0
        reduction_pct = ((orig_size_bytes - new_size_bytes) / orig_size_bytes) * 100.0 if orig_size_bytes > 0 else 0

        return {
            'rel_path': relative_path,
            'orig_kb': orig_size_kb,
            'new_kb': new_size_kb,
            'reduction_pct': reduction_pct,
            'orig_res': f"{orig_w}x{orig_h}",
            'new_res': f"{new_w}x{new_h}",
        }
    except Exception as e:
        print(f"Error optimizing {filepath}: {e}")
        return None

def process_directory(base_dir):
    results = []
    if not os.path.exists(base_dir):
        return results

    for root, dirs, files in os.walk(base_dir):
        for f in files:
            if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp', '.avif')):
                fp = os.path.join(root, f)
                rel = os.path.relpath(fp, os.path.dirname(base_dir))
                res = optimize_file(fp, rel)
                if res:
                    results.append(res)
    return results

if __name__ == '__main__':
    workspace_root = r'd:\Coding\HTML_CSS_JavaScript\Restaurant_Website'
    static_images = os.path.join(workspace_root, 'static', 'images')
    media_products = os.path.join(workspace_root, 'media', 'products')
    media_categories = os.path.join(workspace_root, 'media', 'categories')

    all_results = []
    all_results.extend(process_directory(static_images))
    all_results.extend(process_directory(media_products))
    all_results.extend(process_directory(media_categories))

    total_orig = sum(r['orig_kb'] for r in all_results)
    total_new = sum(r['new_kb'] for r in all_results)
    total_reduction = ((total_orig - total_new) / total_orig) * 100.0 if total_orig > 0 else 0

    print("=" * 95)
    print(f"{'Relative File Path':<45} | {'Original Size':<12} | {'New Size':<12} | {'Reduction':<10} | {'Res Change'}")
    print("=" * 95)
    for r in all_results:
        print(f"{r['rel_path']:<45} | {r['orig_kb']:>8.1f} KB | {r['new_kb']:>8.1f} KB | {r['reduction_pct']:>8.1f}% | {r['orig_res']} -> {r['new_res']}")
    print("=" * 95)
    print(f"TOTAL ORIGINAL PAYLOAD: {total_orig / 1024.0:.2f} MB ({total_orig:.1f} KB)")
    print(f"TOTAL OPTIMIZED PAYLOAD: {total_new / 1024.0:.2f} MB ({total_new:.1f} KB)")
    print(f"OVERALL PAYLOAD REDUCTION: {total_reduction:.1f}%")
    print("=" * 95)
