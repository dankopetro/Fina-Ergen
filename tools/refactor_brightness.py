import json
import os

KEYWORDS_TV = ["televisor", "tv", "tele"]
KEYWORDS_LIGHTS = ["lámpara", "luz", "luces", "foco", "bombilla", "habitación", "proyector", "iluminación"]

def refactor_intents():
    path = "intents.json"
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Initialize new intents if not present
    new_intents = {
        "tv_increase_brightness": [],
        "tv_decrease_brightness": [],
        "lights_increase_brightness": [],
        "lights_decrease_brightness": []
    }
    
    # Process increase_brightness
    original_increase = data.get("increase_brightness", [])
    clean_increase = []
    
    for phrase in original_increase:
        p_lower = phrase.lower()
        is_moved = False
        
        # Check TV
        if any(k in p_lower for k in KEYWORDS_TV):
            new_intents["tv_increase_brightness"].append(phrase)
            is_moved = True
        # Check Lights
        elif any(k in p_lower for k in KEYWORDS_LIGHTS):
            new_intents["lights_increase_brightness"].append(phrase)
            is_moved = True
            
        if not is_moved:
            clean_increase.append(phrase)

    # Process decrease_brightness
    original_decrease = data.get("decrease_brightness", [])
    clean_decrease = []
    
    for phrase in original_decrease:
        p_lower = phrase.lower()
        is_moved = False
        
        # Check TV
        if any(k in p_lower for k in KEYWORDS_TV):
            new_intents["tv_decrease_brightness"].append(phrase)
            is_moved = True
        # Check Lights
        elif any(k in p_lower for k in KEYWORDS_LIGHTS):
            new_intents["lights_decrease_brightness"].append(phrase)
            is_moved = True
            
        if not is_moved:
            clean_decrease.append(phrase)

    # Update data
    data["increase_brightness"] = clean_increase
    data["decrease_brightness"] = clean_decrease
    
    for k, v in new_intents.items():
        if k in data:
            data[k].extend(v)
            # Deduplicate
            data[k] = list(set(data[k]))
        else:
            data[k] = v

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print("Intents refactored successfully.")
    print(f"Moved to tv_increase_brightness: {len(new_intents['tv_increase_brightness'])}")
    print(f"Moved to lights_increase_brightness: {len(new_intents['lights_increase_brightness'])}")
    print(f"Moved to tv_decrease_brightness: {len(new_intents['tv_decrease_brightness'])}")
    print(f"Moved to lights_decrease_brightness: {len(new_intents['lights_decrease_brightness'])}")

if __name__ == "__main__":
    refactor_intents()
