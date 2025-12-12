# %%
import os
import re
import matplotlib.pyplot as plt

# 1. 데이터 저장할 딕셔너리 (벤치마크별로 구분)
benchmarks_data = {}

# 2. 데이터 디렉토리 설정
data_dir = 'datas'

# 파일명 패턴: {benchmark}_s{n}_a{m}.txt (예: equake_s1_a32.txt)
# 그룹 1: 벤치마크 이름, 그룹 2: nsets, 그룹 3: assoc
file_pattern = re.compile(r"([a-zA-Z0-9]+)_s(\d+)_a(\d+)\.txt")

# 디렉토리 존재 여부 확인
if not os.path.exists(data_dir):
    print(f"Error: '{data_dir}' directory not found.")
    exit(1)

# datas 디렉토리의 모든 파일 확인
for filename in os.listdir(data_dir):
    match = file_pattern.search(filename)
    if match:
        benchmark = match.group(1)
        nsets = int(match.group(2))
        assoc = int(match.group(3))
        
        if benchmark not in benchmarks_data:
            benchmarks_data[benchmark] = []

        il1_miss = None
        dl1_miss = None
        
        filepath = os.path.join(data_dir, filename)
        
        # 파일 내용 읽기
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.readlines()
                for line in content:
                    # il1.miss_rate 추출
                    if "il1.miss_rate" in line:
                        parts = line.split()
                        if len(parts) >= 2:
                            il1_miss = float(parts[1])
                    
                    # dl1.miss_rate 추출
                    if "dl1.miss_rate" in line:
                        parts = line.split()
                        if len(parts) >= 2:
                            dl1_miss = float(parts[1])
            
            # 데이터가 정상적으로 추출되었으면 리스트에 추가
            if il1_miss is not None and dl1_miss is not None:
                benchmarks_data[benchmark].append({
                    'nsets': nsets,
                    'assoc': assoc,
                    'il1': il1_miss,
                    'dl1': dl1_miss
                })
                print(f"Extracted: {filename} -> bench={benchmark}, n={nsets}, a={assoc}")
                
        except Exception as e:
            print(f"Error reading {filename}: {e}")

# 데이터가 없으면 종료
if not benchmarks_data:
    print("해당 패턴의 파일을 찾을 수 없습니다.")
else:
    # 각 벤치마크별로 그래프 그리기
    for benchmark, data in benchmarks_data.items():
        if not data:
            continue
            
        print(f"Plotting results for {benchmark}...")
        
        # 3. 데이터 정렬
        data.sort(key=lambda x: (x['assoc'], x['nsets']))

        # 4. 그래프 그리기
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
        fig.suptitle(f'Benchmark: {benchmark}', fontsize=16)

        # 고유한 assoc 값들 추출 (범례용)
        assocs = sorted(list(set(d['assoc'] for d in data)))

        # --- 그래프 1: IL1 Miss Rate ---
        for a in assocs:
            subset = [d for d in data if d['assoc'] == a]
            subset.sort(key=lambda x: x['nsets'])
            
            x_vals = [d['nsets'] for d in subset]
            y_vals = [d['il1'] for d in subset]
            
            ax1.plot(x_vals, y_vals, marker='o', label=f'Assoc {a}')

        ax1.set_title('IL1 Miss Rate vs NSets')
        ax1.set_xlabel('Number of Sets (nsets)')
        ax1.set_ylabel('Miss Rate')
        ax1.set_xscale('log')
        ax1.grid(True, which="both", ls="-", alpha=0.5)
        ax1.legend()

        # --- 그래프 2: DL1 Miss Rate ---
        for a in assocs:
            subset = [d for d in data if d['assoc'] == a]
            subset.sort(key=lambda x: x['nsets'])
            
            x_vals = [d['nsets'] for d in subset]
            y_vals = [d['dl1'] for d in subset]
            
            ax2.plot(x_vals, y_vals, marker='s', label=f'Assoc {a}')

        ax2.set_title('DL1 Miss Rate vs NSets')
        ax2.set_xlabel('Number of Sets (nsets)')
        ax2.set_ylabel('Miss Rate')
        ax2.set_xscale('log')
        ax2.grid(True, which="both", ls="-", alpha=0.5)
        ax2.legend()

        plt.tight_layout()
        #plt.show()
        plt.savefig('my_plot.png') 
        print("그래프가 my_plot.png로 저장되었습니다.")
# %%
