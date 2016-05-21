from importlib import reload
import reloadable

if __name__ == '__main__':
    while True:
        reloadable.run()
        reload(reloadable)
        print("reloaded")
    print("exited")
