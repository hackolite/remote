# remote
Remote python coding made simple :

remote is a python decorator allowing to execute your function remotely or not, asynchronely or not on one server or  on plenty servers, in parralle.


Install the package on client and remote.

    #!/usr/bin/python
    #-*- coding: utf-8 -*-


    import os
    import psutil
    from remote.remote import remoteFunction





    @remoteFunction()
    def toto(path):
        result = os.listdir(path)
        dic_tmp = {
            "memory_total"   : psutil.virtual_memory().total,
            "memory_available" : psutil.virtual_memory().available,
            "memory_percent" : psutil.virtual_memory().percent,
            "memory_used" : psutil.virtual_memory().used,
            "memory_free" : psutil.virtual_memory().free,
            "memory_active" : psutil.virtual_memory().active,
            "memory_inactive" : psutil.virtual_memory().inactive,
            "memory_buffers" : psutil.virtual_memory().buffers,
            "memory_cached" : psutil.virtual_memory().cached
            }
        return dic_tmp



    if __name__ == "__main__":
        ret = toto('.', remote=('host', 'user', 'password'))
        print ret
