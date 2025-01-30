from thread_manager import ThreadManager

def main():
    manager = ThreadManager()
    
    while True:
        print("\n=== X Thread Generator ===")
        print("1. Create new thread")
        print("2. Exit")
        
        choice = input("\nChoice: ")
        
        if choice == "1":
            topic = input("\nWhat would you like the thread to be about? ")
            manager.create_and_post_thread(topic)
        elif choice == "2":
            break
        else:
            print("Invalid choice")

if __name__ == "__main__":
    main() 