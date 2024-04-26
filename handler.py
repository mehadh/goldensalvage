from iaai import handler as iHandler
from carfax import handler as cHandler
from sheetFormat import handler as fHandler
import os, sys
from copart2 import handler as cpHandler

os.chdir(sys.path[0])

def masterHandler():
    # run_iaai = input("Run IAAI? (yes/no): ")
    # if run_iaai.lower() == 'yes':
    #     iaaiResult = iHandler()
    #     if not iaaiResult:
    #         print("IAAI result not come in")
    #         return False
    runCp = input("Run copart? (yes/no): ")
    if runCp.lower() == 'yes':
        cpRes = cpHandler()
        if not cpRes:
            print("copart result not come in")
            return False
    carfaxResult = cHandler(True)
    if not carfaxResult:
        print("Carfax result not come in")
        return False
    
    formatterResult = fHandler(True)
    if not formatterResult:
        print("Formatter result not come in")
        return False
    
    return True
    
if __name__ == "__main__":
    masterHandler()
