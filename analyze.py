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

        # 최적값 찾기 (IL1 + DL1 Miss Rate 합이 최소인 지점)
        # 정렬이 (assoc, nsets) 오름차순이므로, min을 사용하면 동일한 성능일 경우 더 작은 리소스를 사용하는 설정이 선택됨
        best_config = min(data, key=lambda x: x['il1'] + x['dl1'])
        best_info = f"Optimal: nsets={best_config['nsets']}, assoc={best_config['assoc']} (Total Miss: {best_config['il1'] + best_config['dl1']:.4f})"
        print(f"  -> {best_info}")

        # 4. 그래프 그리기
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 7))
        fig.suptitle(f'Benchmark: {benchmark}\n{best_info}', fontsize=14)

        # 고유한 assoc 값들 추출 (범례용)
        assocs = sorted(list(set(d['assoc'] for d in data)))

        # --- 그래프 1: IL1 Miss Rate ---
        for a in assocs:
            subset = [d for d in data if d['assoc'] == a]
            subset.sort(key=lambda x: x['nsets'])
            
            x_vals = [d['nsets'] for d in subset]
            y_vals = [d['il1'] for d in subset]
            
            ax1.plot(x_vals, y_vals, marker='o', label=f'Assoc {a}')

        # 최적점 표시
        ax1.plot(best_config['nsets'], best_config['il1'], 'r*', markersize=15, zorder=10, label='Optimal')

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

        # 최적점 표시
        ax2.plot(best_config['nsets'], best_config['dl1'], 'r*', markersize=15, zorder=10, label='Optimal')

        ax2.set_title('DL1 Miss Rate vs NSets')
        ax2.set_xlabel('Number of Sets (nsets)')
        ax2.set_ylabel('Miss Rate')
        ax2.set_xscale('log')
        ax2.grid(True, which="both", ls="-", alpha=0.5)
        ax2.legend()

        plt.tight_layout()
        output_filename = f'{benchmark}_result.png'
        plt.savefig(output_filename)
        print(f"Saved graph to {output_filename}")
        plt.close(fig)

# 5. 전체 벤치마크 종합 분석 (Global Analysis)
print("\nPerforming Global Analysis...")
global_configs = {} # (nsets, assoc) -> [miss_rates...]

for bench, data_list in benchmarks_data.items():
    for d in data_list:
        key = (d['nsets'], d['assoc'])
        total_miss = d['il1'] + d['dl1']
        if key not in global_configs:
            global_configs[key] = []
        global_configs[key].append(total_miss)

# 평균 계산
avg_data = []
for (nsets, assoc), miss_list in global_configs.items():
    avg_miss = sum(miss_list) / len(miss_list)
    avg_data.append({
        'nsets': nsets,
        'assoc': assoc,
        'avg_miss': avg_miss
    })

avg_data.sort(key=lambda x: (x['assoc'], x['nsets']))

# Global Optimal 찾기
best_global = min(avg_data, key=lambda x: x['avg_miss'])
print(f"Global Optimal: nsets={best_global['nsets']}, assoc={best_global['assoc']}, Avg Miss={best_global['avg_miss']:.4f}")

# Global Average 그래프 그리기
fig_g, ax_g = plt.subplots(figsize=(10, 6))
assocs = sorted(list(set(d['assoc'] for d in avg_data)))

for a in assocs:
    subset = [d for d in avg_data if d['assoc'] == a]
    subset.sort(key=lambda x: x['nsets'])
    x_vals = [d['nsets'] for d in subset]
    y_vals = [d['avg_miss'] for d in subset]
    ax_g.plot(x_vals, y_vals, marker='o', label=f'Assoc {a}')

ax_g.plot(best_global['nsets'], best_global['avg_miss'], 'r*', markersize=15, zorder=10, label='Optimal')
ax_g.set_title(f'Global Average Miss Rate vs NSets\nOptimal: n={best_global["nsets"]}, a={best_global["assoc"]}')
ax_g.set_xlabel('Number of Sets')
ax_g.set_ylabel('Average Total Miss Rate (IL1+DL1)')
ax_g.set_xscale('log')
ax_g.grid(True, which="both", ls="-", alpha=0.5)
ax_g.legend()
plt.tight_layout()
plt.savefig('global_average_result.png')
plt.close(fig_g)
print("Saved global_average_result.png")

# 6. Set vs Assoc Trade-off Analysis (Same Cache Size)
# Cache Size metric ~ nsets * assoc
size_analysis = {} # size -> {'sets_dominant': [], 'assoc_dominant': [], 'equal': []}

for d in avg_data:
    size = d['nsets'] * d['assoc']
    if size not in size_analysis:
        size_analysis[size] = {'sets_dominant': [], 'assoc_dominant': [], 'equal': []}
    
    if d['nsets'] > d['assoc']:
        size_analysis[size]['sets_dominant'].append(d['avg_miss'])
    elif d['assoc'] > d['nsets']:
        size_analysis[size]['assoc_dominant'].append(d['avg_miss'])
    else:
        size_analysis[size]['equal'].append(d['avg_miss'])

sizes = sorted(size_analysis.keys())
sets_dom_vals = []
assoc_dom_vals = []
valid_sizes = []

for s in sizes:
    s_list = size_analysis[s]['sets_dominant']
    a_list = size_analysis[s]['assoc_dominant']
    
    # 데이터가 있는 경우에만 그래프에 포함
    if s_list or a_list:
        valid_sizes.append(s)
        sets_val = sum(s_list)/len(s_list) if s_list else None
        assoc_val = sum(a_list)/len(a_list) if a_list else None
        sets_dom_vals.append(sets_val)
        assoc_dom_vals.append(assoc_val)

fig_t, ax_t = plt.subplots(figsize=(10, 6))
# None 값은 plot에서 자동으로 건너뜀 (연결되지 않음) -> 연결되게 하려면 필터링 필요하지만, 여기선 점으로 표현하거나 끊겨도 무방
# 명확한 비교를 위해 선 그래프 + 마커 사용
ax_t.plot(valid_sizes, sets_dom_vals, marker='o', linestyle='-', label='Sets > Assoc (More Sets)')
ax_t.plot(valid_sizes, assoc_dom_vals, marker='s', linestyle='--', label='Assoc > Sets (More Assoc)')

ax_t.set_title('Impact of Configuration on Miss Rate (Fixed Cache Size)')
ax_t.set_xlabel('Cache Size Index (nsets * assoc)')
ax_t.set_ylabel('Average Total Miss Rate')
ax_t.set_xscale('log')
ax_t.grid(True, which="both", ls="-", alpha=0.5)
ax_t.legend()
plt.tight_layout()
plt.savefig('set_vs_assoc_tradeoff.png')
plt.close(fig_t)
print("Saved set_vs_assoc_tradeoff.png")
