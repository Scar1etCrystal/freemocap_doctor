import sys, pickle
sys.path.insert(0, r'F:\mocap_ai_doctor')
import numpy as np

SRC = r'F:\0001-1499_f_full_20260925_165539等2项文件\0001-1499_f_full_20260925_165539\hamer\merged.pkl'

with open(SRC, 'rb') as f:
    d = pickle.load(f, encoding='latin1')

print('top keys:', list(d.keys()))
for k in d:
    v = d[k]
    if isinstance(v, dict):
        print(f'  {k}: dict keys ->', list(v.keys()))

g = d['smpl_params_incam']
lhp = np.asarray(g['left_hand_pose'])
print('left_hand_pose:', lhp.shape, lhp.dtype)
print('left_hand_is_detected 495-515:', np.asarray(g['left_hand_is_detected'])[495:516].ravel() if 'left_hand_is_detected' in g else 'N/A')

# MANO: index finger = joints 1,2,3 -> cols 3:12 in the 45-dim vector? 
# Wait: spec says 0=wrist is NOT in hand_pose (hand_pose is 15 joints), joints 1-3=index -> cols 3:12? 
# 15 joints x3 =45. index finger joints 1,2,3 => cols (1*3):(4*3)=3:12. Yes.
idx = lhp[:, 3:12].reshape(-1, 3, 3)  # (T, 3 joints, 3)
norms = np.linalg.norm(idx, axis=2)   # (T, 3)
mean_n = norms.mean(axis=1)

def show(a, b):
    print(f'--- frames {a}-{b} index-finger joint rotvec norms (j1 j2 j3) | mean ---')
    for f in range(a, b + 1):
        print(f'{f:4d}  {norms[f,0]:.3f} {norms[f,1]:.3f} {norms[f,2]:.3f}  | {mean_n[f]:.3f}')

show(495, 520)
show(400, 600)
