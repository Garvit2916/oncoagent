"""
Generate realistic, high-fidelity medical scan samples (Brain, Lung, Liver, Pancreas, Colon, Breast)
with distinct anatomical structures, lesions/nodules, and paired ground-truth masks.
"""

import os
import cv2
import numpy as np

def create_scan_canvas(size=512):
    return np.zeros((size, size), dtype=np.uint8)

def generate_brain_mri(has_tumor=True):
    img = create_scan_canvas(512)
    mask = create_scan_canvas(512)
    center = (256, 256)
    
    # Outer skull & scalp
    cv2.ellipse(img, center, (180, 220), 0, 0, 360, 180, 4)
    cv2.ellipse(img, center, (170, 210), 0, 0, 360, 40, -1) # CSF / subarachnoid
    cv2.ellipse(img, center, (165, 205), 0, 0, 360, 110, -1) # Brain parenchyma
    
    # Internal brain structures (gyri / sulci textures)
    noise = np.random.normal(0, 12, (512, 512)).astype(np.float32)
    img_f = img.astype(np.float32) + noise
    img = np.clip(img_f, 0, 255).astype(np.uint8)
    
    # Mask out outside brain
    outside_mask = np.zeros((512, 512), dtype=np.uint8)
    cv2.ellipse(outside_mask, center, (165, 205), 0, 0, 360, 255, -1)
    img = cv2.bitwise_and(img, outside_mask)
    
    # Bilateral ventricles (butterfly CSF spaces)
    cv2.ellipse(img, (240, 250), (12, 45), -15, 0, 360, 30, -1)
    cv2.ellipse(img, (272, 250), (12, 45), 15, 0, 360, 30, -1)
    cv2.line(img, (256, 70), (256, 440), 50, 1) # Interhemispheric fissure
    
    if has_tumor:
        # Focal hyperintense tumor mass with necrotic center and surrounding edema
        t_center = (200, 210)
        cv2.circle(img, t_center, 38, 140, -1) # Edema halo
        cv2.circle(img, t_center, 28, 235, -1) # Contrast-enhancing rim
        cv2.circle(img, t_center, 14, 160, -1) # Central necrosis
        cv2.circle(mask, t_center, 28, 255, -1)
        
    # Smooth anatomical transitions
    img = cv2.GaussianBlur(img, (5, 5), 1.2)
    return img, mask

def generate_lung_ct(has_nodule=True, multiple=False):
    img = create_scan_canvas(512)
    mask = create_scan_canvas(512)
    
    # Body wall & thorax
    cv2.ellipse(img, (256, 256), (220, 175), 0, 0, 360, 130, -1)
    cv2.ellipse(img, (256, 256), (220, 175), 0, 0, 360, 220, 6) # Subcutaneous fat & skin
    
    # Ribs (cortical bone ring)
    for angle in range(0, 360, 30):
        rad = np.deg2rad(angle)
        rx = int(256 + 205 * np.cos(rad))
        ry = int(256 + 160 * np.sin(rad))
        cv2.circle(img, (rx, ry), 8, 250, -1)
        
    # Spine (vertebral body)
    cv2.circle(img, (256, 380), 22, 240, -1)
    cv2.circle(img, (256, 380), 8, 40, -1) # Spinal canal
    
    # Mediastinum (heart / great vessels)
    cv2.ellipse(img, (256, 270), (55, 75), 0, 0, 360, 140, -1)
    cv2.circle(img, (256, 205), 14, 20, -1) # Trachea / carina
    
    # Bilateral lung fields (low attenuation air)
    cv2.ellipse(img, (160, 260), (65, 110), 5, 0, 360, 25, -1)
    cv2.ellipse(img, (352, 260), (65, 110), -5, 0, 360, 25, -1)
    
    # Bronchovascular markings in lungs
    for offset in [-1, 1]:
        cx = 256 + offset * 96
        for i in range(12):
            bx = cx + np.random.randint(-35, 35)
            by = 260 + np.random.randint(-80, 80)
            cv2.circle(img, (bx, by), np.random.randint(2, 4), 90, -1)
            
    if has_nodule:
        # Solitary pulmonary nodule (spiculated mass)
        n_pos = (150, 240)
        cv2.circle(img, n_pos, 22, 215, -1)
        # Spiculations
        for a in range(0, 360, 45):
            rad = np.deg2rad(a)
            ex = int(n_pos[0] + 28 * np.cos(rad))
            ey = int(n_pos[1] + 28 * np.sin(rad))
            cv2.line(img, n_pos, (ex, ey), 190, 2)
        cv2.circle(mask, n_pos, 24, 255, -1)
        
    if multiple:
        # Secondary nodule in contralateral lung
        n2_pos = (360, 290)
        cv2.circle(img, n2_pos, 16, 200, -1)
        cv2.circle(mask, n2_pos, 16, 255, -1)
        
    img = cv2.GaussianBlur(img, (3, 3), 0.8)
    return img, mask

def generate_liver_ct(has_lesion=True):
    img = create_scan_canvas(512)
    mask = create_scan_canvas(512)
    
    # Abdominal wall
    cv2.ellipse(img, (256, 256), (210, 165), 0, 0, 360, 120, -1)
    cv2.ellipse(img, (256, 256), (210, 165), 0, 0, 360, 230, 6)
    
    # Spine & aorta
    cv2.circle(img, (256, 360), 20, 240, -1)
    cv2.circle(img, (240, 320), 12, 190, -1) # Aorta
    
    # Liver parenchyma (occupying right upper quadrant)
    pts = np.array([
        [100, 220], [130, 160], [210, 140], [270, 180],
        [280, 280], [240, 330], [150, 340], [95, 290]
    ], np.int32)
    cv2.fillPoly(img, [pts], 155)
    
    # Spleen (left upper quadrant)
    cv2.ellipse(img, (380, 230), (35, 60), 25, 0, 360, 140, -1)
    
    # Portal venous branches
    cv2.line(img, (200, 220), (140, 210), 195, 4)
    cv2.line(img, (200, 220), (170, 270), 195, 3)
    
    if has_lesion:
        # Hypodense liver lesion (hepatocellular carcinoma / metastasis)
        l_pos = (180, 230)
        cv2.circle(img, l_pos, 32, 85, -1) # Hypodense core
        cv2.circle(img, l_pos, 32, 195, 3) # Arterial rim enhancement
        cv2.circle(mask, l_pos, 32, 255, -1)
        
    img = cv2.GaussianBlur(img, (3, 3), 0.8)
    return img, mask

def generate_pancreas_ct(has_mass=True):
    img = create_scan_canvas(512)
    mask = create_scan_canvas(512)
    
    # Body wall
    cv2.ellipse(img, (256, 256), (210, 160), 0, 0, 360, 110, -1)
    cv2.ellipse(img, (256, 256), (210, 160), 0, 0, 360, 220, 5)
    
    # Spine & vessels
    cv2.circle(img, (256, 350), 20, 240, -1)
    cv2.circle(img, (245, 305), 11, 200, -1) # Aorta
    cv2.circle(img, (270, 305), 11, 180, -1) # IVC
    
    # Pancreatic parenchyma (draped across retroperitoneum)
    cv2.ellipse(img, (245, 260), (60, 18), -15, 0, 360, 130, -1)
    cv2.ellipse(img, (290, 250), (35, 14), -25, 0, 360, 130, -1) # Pancreatic tail
    
    # Stomach (anterior)
    cv2.ellipse(img, (230, 190), (65, 30), 10, 0, 360, 45, -1)
    
    if has_mass:
        # Pancreatic head ductal adenocarcinoma
        p_pos = (215, 265)
        cv2.circle(img, p_pos, 25, 185, -1)
        cv2.circle(mask, p_pos, 25, 255, -1)
        
    img = cv2.GaussianBlur(img, (3, 3), 0.8)
    return img, mask

def generate_colon_ct(has_mass=True):
    img = create_scan_canvas(512)
    mask = create_scan_canvas(512)
    
    # Pelvic / abdominal wall
    cv2.ellipse(img, (256, 256), (205, 170), 0, 0, 360, 115, -1)
    cv2.ellipse(img, (256, 256), (205, 170), 0, 0, 360, 225, 5)
    
    # Spine / sacrum
    cv2.circle(img, (256, 370), 22, 235, -1)
    
    # Small bowel loops with air/fluid levels
    for b_pos in [(210, 230), (280, 220), (250, 280), (310, 280)]:
        cv2.circle(img, b_pos, 24, 70, -1)
        cv2.circle(img, (b_pos[0], b_pos[1]-6), 14, 20, -1)
        
    # Descending colon lumen
    c_pos = (350, 260)
    cv2.circle(img, c_pos, 30, 110, -1)
    cv2.circle(img, c_pos, 20, 25, -1)
    
    if has_mass:
        # Annular constricting colonic wall thickening mass ("apple-core")
        cv2.circle(img, c_pos, 35, 190, -1)
        cv2.circle(img, c_pos, 8, 20, -1) # Narrowed lumen
        cv2.circle(mask, c_pos, 32, 255, -1)
        
    img = cv2.GaussianBlur(img, (3, 3), 0.8)
    return img, mask

def generate_breast_mammogram(has_mass=True):
    img = create_scan_canvas(512)
    mask = create_scan_canvas(512)
    
    # Pectoral muscle shadow in upper left
    pts_pectoral = np.array([[0, 0], [210, 0], [0, 260]], np.int32)
    cv2.fillPoly(img, [pts_pectoral], 160)
    
    # Fibroglandular breast contour
    pts_breast = np.array([
        [0, 60], [230, 120], [380, 260], [420, 360],
        [370, 460], [220, 510], [0, 510]
    ], np.int32)
    cv2.fillPoly(img, [pts_breast], 65)
    
    # Dense fibroglandular parenchyma texture
    for _ in range(40):
        fx = np.random.randint(80, 320)
        fy = np.random.randint(180, 450)
        cv2.ellipse(img, (fx, fy), (np.random.randint(15, 45), np.random.randint(8, 25)), np.random.randint(0, 180), 0, 360, np.random.randint(80, 130), -1)
        
    if has_mass:
        # High-density spiculated breast mass with microcalcifications
        b_pos = (280, 320)
        cv2.circle(img, b_pos, 26, 220, -1)
        # Spiculated margins
        for a in range(0, 360, 30):
            rad = np.deg2rad(a)
            ex = int(b_pos[0] + 36 * np.cos(rad))
            ey = int(b_pos[1] + 36 * np.sin(rad))
            cv2.line(img, b_pos, (ex, ey), 195, 2)
        # Microcalcifications inside mass
        for _ in range(8):
            mx = b_pos[0] + np.random.randint(-12, 12)
            my = b_pos[1] + np.random.randint(-12, 12)
            cv2.circle(img, (mx, my), 2, 255, -1)
        cv2.circle(mask, b_pos, 28, 255, -1)
        
    img = cv2.GaussianBlur(img, (3, 3), 0.8)
    return img, mask


def main():
    target_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "tests", "sample_scans")
    os.makedirs(target_dir, exist_ok=True)
    
    samples = [
        ("01_lung_ct_with_nodule.png", lambda: generate_lung_ct(has_nodule=True, multiple=False)),
        ("02_lung_ct_normal.png", lambda: generate_lung_ct(has_nodule=False)),
        ("03_lung_ct_multiple_nodules.png", lambda: generate_lung_ct(has_nodule=True, multiple=True)),
        ("04_brain_mri_with_tumor.png", lambda: generate_brain_mri(has_tumor=True)),
        ("05_brain_mri_normal.png", lambda: generate_brain_mri(has_tumor=False)),
        ("06_liver_ct_with_lesion.png", lambda: generate_liver_ct(has_lesion=True)),
        ("07_liver_ct_normal.png", lambda: generate_liver_ct(has_lesion=False)),
        ("08_pancreas_ct_with_mass.png", lambda: generate_pancreas_ct(has_mass=True)),
        ("09_pancreas_ct_normal.png", lambda: generate_pancreas_ct(has_mass=False)),
        ("10_colon_ct_with_mass.png", lambda: generate_colon_ct(has_mass=True)),
        ("11_colon_ct_normal.png", lambda: generate_colon_ct(has_mass=False)),
        ("12_breast_mammogram_with_mass.png", lambda: generate_breast_mammogram(has_mass=True)),
        ("13_breast_mammogram_normal.png", lambda: generate_breast_mammogram(has_mass=False)),
    ]
    
    print(f"Generating {len(samples)} realistic medical scans in {target_dir}...")
    for filename, gen_fn in samples:
        img, mask = gen_fn()
        img_path = os.path.join(target_dir, filename)
        cv2.imwrite(img_path, img)
        mask_filename = filename.replace(".png", "_mask.png")
        mask_path = os.path.join(target_dir, mask_filename)
        cv2.imwrite(mask_path, mask)
        print(f"  [OK] {filename:36} (mask: {int((mask > 0).sum())} px)")

if __name__ == "__main__":
    main()
