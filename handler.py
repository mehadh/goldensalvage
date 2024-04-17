from iaai import handler as iHandler
from carfax import handler as cHandler
from sheetFormat import handler as fHandler
import os, sys
os.chdir(sys.path[0])

def masterHandler():
    iaaiResult = iHandler()
    if not iaaiResult:
        print("iaai result not come in")
        return False
    carfaxResult = cHandler(True)
    if not carfaxResult:
        print("carfax result not come in")
        return False
    formatterResult = fHandler(True)
    if not formatterResult:
        print("formatter result not come in")
        return False
    return True
    
if __name__ == "__main__":
    masterHandler()