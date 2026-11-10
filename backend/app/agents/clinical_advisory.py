"""
Simplified, Patient-Friendly Clinical Advisory Module for Pan-Organ AI Dashboard.
Provides easy-to-understand explanations of scan results, recommended doctors,
common medicines, and simple next steps for patients and family members.
"""

PATIENT_FRIENDLY_ADVISORY = {
    "Brain": {
        "organ_display": "Brain",
        "urgency_level": "Important — Please Visit a Specialist Soon",
        "urgency_color": "#e53935",
        "simple_title": "Suspected Brain Growth / Tumor",
        "what_this_means": "The AI detected a suspicious growth in the brain area. While this requires medical attention, early detection allows doctors to choose the most effective treatment plan.",
        "doctors": [
            {
                "name": "Brain Tumor Specialist (Neuro-Oncologist)",
                "department": "Cancer & Neurology Center",
                "why_visit": "This is the main doctor who specializes in treating brain tumors and guiding your overall medicine and recovery plan."
            },
            {
                "name": "Brain Surgeon (Neurosurgeon)",
                "department": "Neurosurgery Department",
                "why_visit": "Examines the scan to see if the growth can be safely removed or if a small sample (biopsy) should be tested."
            }
        ],
        "medications": [
            {
                "name": "Temozolomide (TMZ)",
                "type": "Chemotherapy Pill",
                "what_it_does": "A daily capsule that specifically targets and helps shrink brain tumor cells.",
                "simple_tip": "Usually taken on an empty stomach with plenty of water as prescribed."
            },
            {
                "name": "Dexamethasone",
                "type": "Swelling Reducer (Steroid)",
                "what_it_does": "Reduces swelling and pressure inside the head to quickly relieve headaches, dizziness, and nausea.",
                "simple_tip": "Take with meals to prevent stomach irritation; do not stop taking it suddenly."
            },
            {
                "name": "Levetiracetam (Keppra)",
                "type": "Seizure Prevention Medicine",
                "what_it_does": "Protects against sudden seizures or fits that can sometimes happen with brain growths.",
                "simple_tip": "Take at the same time every day to keep protection steady."
            }
        ],
        "simple_steps": [
            "Book an appointment with a Brain Tumor Specialist (Neuro-Oncologist).",
            "Bring this scan image and any previous medical test records with you to your visit.",
            "Your doctor may order a follow-up contrast MRI scan or a simple biopsy to confirm the exact type.",
            "Bring a family member or friend with you to the appointment to help take notes and support you."
        ]
    },
    "Lung": {
        "organ_display": "Lung",
        "urgency_level": "Important — Please Visit a Specialist Soon",
        "urgency_color": "#e53935",
        "simple_title": "Suspected Lung Spot / Tumor",
        "what_this_means": "The AI detected an abnormal spot or growth in the lung. Finding this early helps your medical team quickly determine the best care.",
        "doctors": [
            {
                "name": "Lung Specialist (Pulmonologist)",
                "department": "Chest & Respiratory Medicine",
                "why_visit": "Checks your breathing, tests lung function, and performs preliminary diagnostic tests."
            },
            {
                "name": "Lung Cancer Doctor (Thoracic Oncologist)",
                "department": "Cancer Care Department",
                "why_visit": "Designs personalized medicine plans (such as targeted therapy or immunotherapy) to treat lung tumors."
            },
            {
                "name": "Chest Surgeon (Thoracic Surgeon)",
                "department": "Thoracic Surgery",
                "why_visit": "Evaluates whether the spot can be safely removed with minimally invasive surgery."
            }
        ],
        "medications": [
            {
                "name": "Immunotherapy (e.g. Pembrolizumab / Keytruda)",
                "type": "Immune-Boosting Medicine",
                "what_it_does": "Trains your body's own immune system to recognize, attack, and destroy lung cancer cells.",
                "simple_tip": "Given via IV infusion every few weeks in a comfortable day-care clinic."
            },
            {
                "name": "Targeted Therapy Pills (e.g. Osimertinib)",
                "type": "Precision Daily Tablet",
                "what_it_does": "Daily pills specifically designed to block the growth signals of certain lung tumors with fewer side effects.",
                "simple_tip": "Only prescribed if specific genetic markers are found in the tumor."
            },
            {
                "name": "Chemotherapy (e.g. Carboplatin + Pemetrexed)",
                "type": "Standard Cancer Medicine",
                "what_it_does": "Powerful medicine that circulates in the bloodstream to stop cancer cells from multiplying.",
                "simple_tip": "Your doctor will give you anti-nausea medicines beforehand to keep you comfortable."
            }
        ],
        "simple_steps": [
            "Schedule a consultation with a Lung Specialist (Pulmonologist).",
            "The doctor will likely recommend a detailed chest CT scan and a minor breathing test.",
            "Avoid smoking and stay away from secondhand smoke, dust, and harsh fumes.",
            "Keep a notebook of any cough, chest discomfort, or breathing changes to tell your doctor."
        ]
    },
    "Liver": {
        "organ_display": "Liver",
        "urgency_level": "Important — Please Visit a Specialist Soon",
        "urgency_color": "#e53935",
        "simple_title": "Suspected Liver Growth / Tumor",
        "what_this_means": "The AI localized an abnormal growth inside the liver. A specialist will check liver health and recommend the best treatment.",
        "doctors": [
            {
                "name": "Liver Specialist (Hepatologist)",
                "department": "Liver & Digestive Health Clinic",
                "why_visit": "Checks your overall liver function and runs blood tests to see how healthy the liver is."
            },
            {
                "name": "Liver Surgeon (HPB Surgeon)",
                "department": "Liver Surgery Department",
                "why_visit": "Determines if the growth can be removed with surgery or specialized heat/radio wave treatments."
            }
        ],
        "medications": [
            {
                "name": "Targeted Liver Pills (e.g. Lenvatinib / Sorafenib)",
                "type": "Targeted Daily Capsule",
                "what_it_does": "Cuts off the blood supply that feeds liver tumors, helping slow down their growth.",
                "simple_tip": "Take daily as directed; your doctor will regularly check your blood pressure."
            },
            {
                "name": "Immunotherapy Combo (Atezolizumab + Bevacizumab)",
                "type": "Advanced Dual Treatment",
                "what_it_does": "Combines immune-system defense with blood-vessel blocking medicine for maximum effectiveness.",
                "simple_tip": "Given by IV infusion in a specialized cancer center."
            },
            {
                "name": "Water Balance Pills (Spironolactone)",
                "type": "Liver Support Tablet",
                "what_it_does": "Helps your body remove extra fluid and prevent swelling in the stomach and legs.",
                "simple_tip": "Drink plenty of water and follow a low-salt diet."
            }
        ],
        "simple_steps": [
            "Visit a Liver Specialist (Hepatologist) for a comprehensive evaluation.",
            "Get standard liver blood tests (including AFP liver marker) and a detailed dynamic scan.",
            "Avoid alcohol and check with your doctor before taking any over-the-counter painkillers.",
            "Eat fresh, balanced meals with low sodium (salt) to support your liver."
        ]
    },
    "Pancreas": {
        "organ_display": "Pancreas",
        "urgency_level": "High Priority — Prompt Doctor Visit Advised",
        "urgency_color": "#d32f2f",
        "simple_title": "Suspected Pancreatic Growth",
        "what_this_means": "The AI detected an abnormal area in the pancreas. Quick evaluation by a pancreatic team ensures the fastest, most effective care.",
        "doctors": [
            {
                "name": "Digestive Cancer Specialist (GI Oncologist)",
                "department": "Digestive Oncology Center",
                "why_visit": "Leads your overall treatment plan and chooses the most effective medicines to shrink the growth."
            },
            {
                "name": "Pancreatic Surgeon (HPB Specialist)",
                "department": "Surgical Oncology",
                "why_visit": "Assesses if surgical removal (such as a Whipple procedure) is possible."
            }
        ],
        "medications": [
            {
                "name": "Combination Chemotherapy (e.g. FOLFIRINOX or Gemcitabine)",
                "type": "Cancer Shrinking Regimen",
                "what_it_does": "A powerful combination of medicines given to effectively shrink pancreatic tumor cells.",
                "simple_tip": "Given on specific scheduled cycle days with rest periods in between."
            },
            {
                "name": "Digestive Enzyme Capsules (Creon / Pancreatin)",
                "type": "Digestive Helper Capsule",
                "what_it_does": "Helps your stomach digest food and absorb nutrients, preventing weight loss and stomach discomfort.",
                "simple_tip": "Swallow these capsules during meals and snacks."
            },
            {
                "name": "Comfort & Pain Relief Medicine",
                "type": "Pain Management Support",
                "what_it_does": "Keeps you feeling comfortable and eliminates back or abdominal discomfort.",
                "simple_tip": "Take as prescribed; do not wait until pain becomes severe."
            }
        ],
        "simple_steps": [
            "Book an appointment with a Digestive Cancer Specialist right away.",
            "Get a specialized high-detail pancreas scan (Pancreas-Protocol CT) to check exact dimensions.",
            "Eat smaller, frequent meals throughout the day to help easy digestion.",
            "Stay well-hydrated with water, broths, and clear juices."
        ]
    },
    "Colon": {
        "organ_display": "Colon (Large Intestine)",
        "urgency_level": "Important — Please Visit a Specialist Soon",
        "urgency_color": "#e53935",
        "simple_title": "Suspected Colon Growth / Polyp",
        "what_this_means": "The AI detected an abnormal lump or growth in the colon (bowel). Colon growths are very treatable, especially when caught early.",
        "doctors": [
            {
                "name": "Stomach & Bowel Specialist (Gastroenterologist)",
                "department": "Gastroenterology Clinic",
                "why_visit": "Performs a gentle colonoscopy exam to look inside the bowel and take a small tissue sample."
            },
            {
                "name": "Bowel Surgeon (Colorectal Surgeon)",
                "department": "Colorectal Surgery",
                "why_visit": "Specializes in minimally invasive surgery to remove colon polyps or growths safely."
            },
            {
                "name": "Cancer Specialist (Medical Oncologist)",
                "department": "Medical Oncology",
                "why_visit": "Guides supportive medicines or chemotherapy if needed to prevent recurrence."
            }
        ],
        "medications": [
            {
                "name": "FOLFOX / Capecitabine",
                "type": "Standard Bowel Cancer Medicine",
                "what_it_does": "Medicines that target fast-growing cells in the colon to shrink tumors and prevent them from spreading.",
                "simple_tip": "Available as IV infusions or oral tablets depending on doctor's recommendation."
            },
            {
                "name": "Targeted Biotherapy (e.g. Bevacizumab / Cetuximab)",
                "type": "Blood-Vessel Blocking Medicine",
                "what_it_does": "Prevents the growth of new blood vessels feeding the tumor.",
                "simple_tip": "Often paired with standard medicines for greater effectiveness."
            }
        ],
        "simple_steps": [
            "Consult a Gastroenterologist (Bowel Specialist) for an evaluation.",
            "Schedule a standard Colonoscopy test so the doctor can directly examine the area.",
            "Get simple routine blood tests (including iron levels and CEA marker).",
            "Drink plenty of water and eat easily digestible, nutritious meals."
        ]
    },
    "Breast": {
        "organ_display": "Breast",
        "urgency_level": "Important — Please Visit a Specialist Soon",
        "urgency_color": "#e53935",
        "simple_title": "Suspected Breast Lump / Tumor",
        "what_this_means": "The AI identified a suspicious lump in the breast tissue. Most breast growths have highly effective, straightforward treatment options.",
        "doctors": [
            {
                "name": "Breast Specialist (Breast Surgeon)",
                "department": "Breast Care Center / Women's Clinic",
                "why_visit": "Examines the lump, arranges imaging, and discusses gentle surgical options (like lumpectomy)."
            },
            {
                "name": "Breast Cancer Doctor (Medical Oncologist)",
                "department": "Medical Oncology",
                "why_visit": "Designs medicine treatments, such as daily hormone blocker tablets or targeted therapies."
            }
        ],
        "medications": [
            {
                "name": "Hormone-Blocking Pills (e.g. Tamoxifen / Letrozole)",
                "type": "Daily Hormone Tablet",
                "what_it_does": "Blocks estrogen hormones that help certain types of breast cells grow.",
                "simple_tip": "A simple daily pill taken with water; highly effective for hormone-positive tumors."
            },
            {
                "name": "Targeted Therapy (e.g. Trastuzumab / Herceptin)",
                "type": "HER2 Protein Blocker",
                "what_it_does": "Specifically targets HER2 proteins found on the surface of certain breast tumor cells.",
                "simple_tip": "Very gentle on normal body cells because it targets only specific tumor proteins."
            },
            {
                "name": "Standard Chemotherapy (AC-T Regimen)",
                "type": "Comprehensive Cancer Medicine",
                "what_it_does": "Given before or after surgery to completely clear any abnormal cells and ensure full recovery.",
                "simple_tip": "Your care team will give supportive medications to keep side effects minimal."
            }
        ],
        "simple_steps": [
            "Visit a Breast Specialist or Women's Health Clinic for a physical checkup.",
            "Have a diagnostic Mammogram or Breast Ultrasound done for clear detailed pictures.",
            "Your doctor may take a gentle needle sample (biopsy) to test the exact cell type.",
            "Remember that modern breast treatments are extremely effective and customizable."
        ]
    }
}

CLEAR_SCAN_SIMPLE = {
    "organ_display": "Healthy Scan",
    "urgency_level": "Normal — No Tumor Detected",
    "urgency_color": "#4caf50",
    "simple_title": "Clear Scan (No Tumors Found)",
    "what_this_means": "Great news! The AI analyzed your scan and did not find any suspicious tumor or abnormal growth.",
    "doctors": [
        {
            "name": "Primary Care Doctor / Family Physician",
            "department": "General Medicine Clinic",
            "why_visit": "For your regular annual health checkups and general wellness advice."
        }
    ],
    "medications": [
        {
            "name": "No Cancer Medications Needed",
            "type": "Healthy Routine",
            "what_it_does": "Your scan looks normal. You do not need any tumor-related treatments.",
            "simple_tip": "Continue any regular daily vitamins or standard medicines you usually take."
        }
    ],
    "simple_steps": [
        "Save this scan image in your personal records as a healthy baseline.",
        "Continue your routine yearly medical checkups as recommended for your age.",
        "Maintain a healthy lifestyle with nutritious foods, regular walking/exercise, and good sleep.",
        "If you ever feel persistent new symptoms or unexplained pain in the future, visit your doctor for a checkup."
    ]
}

def generate_clinical_summary(organ_name: str, has_tumor: bool, confidence: float) -> dict:
    """
    Generates a simple, easy-to-read summary for patients and non-medical users.
    """
    conf_pct = round(confidence * 100, 1)
    
    if not has_tumor or organ_name not in PATIENT_FRIENDLY_ADVISORY:
        data = CLEAR_SCAN_SIMPLE
        summary_text = (
            f"✅ Good news! The AI scan is clear. No tumors or suspicious growths were found in this image "
            f"(Confidence: {conf_pct}%). Everything appears normal. Keep up with your regular healthy lifestyle and standard checkups!"
        )
        return {
            "organ_name": organ_name if organ_name != "Unknown" else "Screening",
            "organ_display": data["organ_display"],
            "has_tumor": False,
            "confidence_pct": conf_pct,
            "urgency_level": data["urgency_level"],
            "urgency_color": data["urgency_color"],
            "simple_title": data["simple_title"],
            "what_this_means": data["what_this_means"],
            "diagnostic_summary": summary_text,
            "doctors": data["doctors"],
            "medications": data["medications"],
            "simple_steps": data["simple_steps"],
            "friendly_disclaimer": "This report is generated by AI to help guide you. Please consult a qualified doctor for an official diagnosis and personalized advice."
        }
    
    data = PATIENT_FRIENDLY_ADVISORY[organ_name]
    summary_text = (
        f"🔍 The AI found a suspected tumor in the {data['organ_display']} with {conf_pct}% confidence. "
        f"The red highlighted area in the image shows where the growth was localized. "
        f"Please schedule a visit with a specialist doctor soon so they can examine this scan and recommend the best next steps."
    )
    
    return {
        "organ_name": organ_name,
        "organ_display": data["organ_display"],
        "has_tumor": True,
        "confidence_pct": conf_pct,
        "urgency_level": data["urgency_level"],
        "urgency_color": data["urgency_color"],
        "simple_title": data["simple_title"],
        "what_this_means": data["what_this_means"],
        "diagnostic_summary": summary_text,
        "doctors": data["doctors"],
        "medications": data["medications"],
        "simple_steps": data["simple_steps"],
        "friendly_disclaimer": "This report is generated by AI to help guide you. Please consult a qualified doctor for an official diagnosis and personalized advice."
    }
