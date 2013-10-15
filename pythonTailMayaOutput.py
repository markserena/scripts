import time, datetime
def follow(thefile):
    thefile.seek(0,1)      # Go to the end of the file
    while True:
         line = thefile.readline()
         if not line:
             time.sleep(1)    # Sleep briefly
             continue
         yield line

list = []
logfile = open("C:\MayaOutputWindow.txt")
loglines = follow(logfile)
newlog = open("C:\MayaOutputWindow2.txt", "w")
for line in loglines:
    newlog.write(str(datetime.datetime.now()) + " :: " + str(line))
newlog.close()    
    
