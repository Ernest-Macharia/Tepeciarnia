# import subprocess
# from pathlib import Path
# from typing import Optional

# from utils.path_utils import BASE_DIR

# class AutoPauseController:
#     def __init__(self):
#         self.proc = None

#     def autopause_path(self) -> Optional[Path]:
#         candidates = [
#             BASE_DIR / "bin" / "tools" / "autopause.exe",
#             BASE_DIR / "bin" / "tools" / "autopause",
#         ]
#         for c in candidates:
#             if c.exists():
#                 return c
#         return None

#     def start(self) -> bool:
#         path = self.autopause_path()
#         if path:
#             try:
#                 self.proc = subprocess.Popen([str(path)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
#                 return True
#             except Exception:
#                 self.proc = None
#         return False

#     def stop(self):
#         if self.proc:
#             try:
#                 self.proc.terminate()
#             except Exception:
#                 pass
#             self.proc = None