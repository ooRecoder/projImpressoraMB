from utils import LockApp

def main():
    singleton = LockApp()
    
    if singleton.is_already_running():
        return

    

if __name__ == "__main__":
    main()