import sqlite3
import uuid
from queue import Queue

class Database:
    def addUser(self, email, password, firstName, lastName):
        conn = sqlite3.connect('app.sqlite')
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users WHERE email=?", (email,))
        if cursor.fetchone()[0] == 0:
            id = None
            #create distinct UUID
            while True:
                validate = uuid.uuid4()
                cursor.execute("SELECT COUNT(*) FROM users WHERE UUID=?", (validate.hex,))
                if cursor.fetchone()[0] == 0:
                    id = validate.hex
                    break
            cursor.execute("INSERT INTO users (UUID, email, password, firstName, lastName) VALUES(?, ?, ?, ?, ?)", (id, email, password, firstName, lastName))
            #create default folder
            conn.commit()
            conn.close()
            self.addFolder(id, "Root", None)
            return True
        conn.close()
        return False
    
    def userByEmail(self, email):
        conn = sqlite3.connect('app.sqlite')
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users WHERE email=?", (email,))
        if cursor.fetchone()[0] > 0:
            cursor.execute("SELECT * FROM users WHERE email=?",(email,))
            data = cursor.fetchone()
            conn.close()
            return data
        return None

    def userByUUID(self, uuid):
        conn = sqlite3.connect('app.sqlite')
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users WHERE UUID=?", (uuid,))
        if cursor.fetchone()[0] > 0:
            cursor.execute("SELECT * FROM users WHERE UUID=?", (uuid,))
            data = cursor.fetchone()
            conn.close()
            return data
        return None
        
    def addFile(self, uuid, filename, data, mimetype, folder):
        conn = sqlite3.connect('app.sqlite')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO files (UUID, filename, data, mimetype, folder) VALUES(?, ?, ?, ?, ?)", (uuid, filename, sqlite3.Binary(data.read()), mimetype, folder))
        conn.commit()
        conn.close()

    def getFile(self, id):
        conn = sqlite3.connect('app.sqlite')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM files WHERE id=?", (id, ))
        data = cursor.fetchone()
        conn.close()
        return data

    def getAllFiles(self, uuid):
        conn = sqlite3.connect('app.sqlite')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM files WHERE UUID=?", (uuid,))
        files = cursor.fetchall()
        conn.close()
        return files

    def getFilesByFolder(self, uuid, folderUUID):
        conn = sqlite3.connect('app.sqlite')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM files WHERE UUID=? AND folder=?", (uuid, folderUUID))
        folders = cursor.fetchall()
        conn.close()
        return folders

    def addFolder(self, userUUID, foldername, parent):
        conn = sqlite3.connect('app.sqlite')
        cursor = conn.cursor()
        id = None
        while True:
            validate = uuid.uuid4()
            cursor.execute("SELECT COUNT(*) FROM folders WHERE UUID=?", (validate.hex,))
            if cursor.fetchone()[0] == 0:
                id = validate.hex
                break
        if parent != None:
            cursor.execute("INSERT INTO folders (userUUID, foldername, UUID, parent) VALUES(?, ?, ?, ?)", (userUUID, foldername, id, parent))
        else:
            cursor.execute("INSERT INTO folders (userUUID, foldername, UUID, parent) VALUES(?, ?, ?, ?)", (userUUID, foldername, id, id))
        conn.commit()
        conn.close()

    def getFolder(self, userUUID, folderUUID):
        conn = sqlite3.connect('app.sqlite')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM folders WHERE userUUID=? AND UUID=?", (userUUID, folderUUID))
        folder = cursor.fetchone()
        conn.close()
        return folder
    
    def getAllFolders(self, userUUID):
        conn = sqlite3.connect('app.sqlite')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM folders WHERE userUUID=?", (userUUID,))
        folders = cursor.fetchall()
        conn.close()
        return folders
    
    def getFoldersByParent(self, userUUID, parent):
        conn = sqlite3.connect('app.sqlite')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM folders WHERE userUUID=? AND parent=?", (userUUID, parent))
        folders = cursor.fetchall()
        cursor.execute("SELECT * FROM folders WHERE userUUID=? AND parent=? AND UUID=?", (userUUID, parent, parent))
        root = cursor.fetchone()
        if root:
            folders.remove(root)
        conn.close()
        return folders

    def getRoot(self, userUUID):
        conn = sqlite3.connect('app.sqlite')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM folders WHERE userUUID=?", (userUUID,))
        #find the root
        for folder in cursor.fetchall():
            if folder[2] == folder[3]:
                conn.close()
                return folder
        conn.close()
        return None  
    
    def getPath(self, userUUID, folderUUID):
        root = self.getRoot(userUUID)
        conn = sqlite3.connect('app.sqlite')
        cursor = conn.cursor()
        curr = folderUUID
        ret = []
        while curr != root[2]:
            cursor.execute("SELECT * FROM folders WHERE userUUID=? AND UUID=?", (userUUID, curr))
            folder = cursor.fetchone()
            ret.append(folder)
            curr = folder[3]
            print("running")
        ret.append(root)
        ret.reverse()
        conn.close()
        return ret

    def deleteFile(self, userUUUID, id):
        conn = sqlite3.connect('app.sqlite')
        cursor = conn.cursor()
        cursor.execute("DELETE FROM files WHERE id=?", (id,))
        conn.commit()
        conn.close()

    #need to add dfs to delete all subfolders
    def deleteFolder(self, userUUID, folderUUID):
        conn = sqlite3.connect('app.sqlite')
        cursor = conn.cursor()
        queue = Queue(0)
        queue.put(folderUUID)
        while not queue.empty():
            curr = queue.get()
            cursor.execute("SELECT * FROM folders WHERE userUUID=? AND parent=?", (userUUID, curr))
            for folder in cursor.fetchall():
                queue.put(folder[2])
            cursor.execute("DELETE FROM folders WHERE userUUID=? AND UUID=?", (userUUID, curr,))
            cursor.execute("DELETE FROM files WHERE UUID=? AND folder=?", (userUUID, curr,))
        conn.commit()
        conn.close()
            
        