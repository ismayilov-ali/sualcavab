
def duzsual():
    with open("txt/sualar.txt", "r", encoding="utf-8") as f:
        sualar = []
        alt_sualar = []
        n = 1
        
        lines = f.readlines()
        
        for line in lines:
            line = line.strip()
            if not line: continue
            
            if line.startswith(f"{n}."):
                if alt_sualar:
                    sualar.append(alt_sualar)
                
                alt_sualar = [line]
                n += 1
            else:
                alt_sualar.append(line)
                
        if alt_sualar:
            sualar.append(alt_sualar)
    return sualar

print(duzsual())