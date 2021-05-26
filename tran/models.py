
import hashlib
import math
import time

import requests
from django.core.handlers.wsgi import WSGIRequest

# Create your models here.
from tran.chinese_dict import data

def get_a_fridenly_word(w:str)->str:
    return data[w.__hash__()%len(data)]
def avsplit(s, n):
    fn = len(s)//n
    rn = len(s)%n
    sr = []
    ix = 0
    for i in range(n):
        if i<rn:
            sr.append(s[ix:ix+fn+1])
            ix += fn+1
        else:
            sr.append(s[ix:ix+fn])
            ix += fn
    return sr

def get_a_friendly_uuid(w:str)->str:
    p=avsplit(w,4)
    return "/"+"/".join([get_a_fridenly_word(p[i]) for i in range(3)])+"/"+str(p[3].__hash__()%10000)

def strcmp_TTAsafety(a:str,b:str)->bool: # A stupid way to defense Timing Attack
    res=True
    for index in range(min(len(a),len(b))):
        res&=(a[index]==b[index])
    return res

class PostFileForm:
    class PwdValidRes:
        CORRECT = 1
        WRONG_PASSWORD = 0
        WRONG_CAPTCHA = -1
        INVALID_FORM = -2
    class ConnRes:
        OK=0
        UNKNOWN=1
        FAIL=-1
    latest_connection_result:ConnRes
    latest_connection_latency:float
    ip:str
    port:int
    filename:str
    captcha:str
    password:str
    hash: str
    update_time: float
    create_time: float
    contribution=0
    def __init__(self,req:WSGIRequest):
        self.ip = req.POST["ip"]
        self.port = req.POST["port"]
        self.filename = req.POST["filename"]
        self.captcha = req.POST["captcha"]
        self.password = req.POST.get("password", None)
        self.check_connection()
        self.hash=None
        self.update_time=time.time()
        self.create_time=time.time()



    def validate_captcha(self,req:WSGIRequest)->bool:
        return hashlib.md5((self.ip + str(self.port) + self.filename + str(req.POST.get("captcha",None))).encode("utf8")).hexdigest().startswith("000")

    def validate_password(self,req:WSGIRequest) -> PwdValidRes:
        try:
            if strcmp_TTAsafety(self.password,str(req.POST.get("password",None))):
                if self.validate_captcha(req):
                    return PostFileForm.PwdValidRes.CORRECT
                else:
                    return PostFileForm.PwdValidRes.WRONG_CAPTCHA
            else:
                return PostFileForm.PwdValidRes.WRONG_PASSWORD
        except:
            return PostFileForm.PwdValidRes.INVALID_FORM

    def get_friendly_uuid(self)->str:
        uuid = get_a_friendly_uuid(self.ip + str(self.port) + self.filename)
        return uuid
    def have_password(self)->bool:
        return (not (self.password==None or self.password==''))
    def is_ipv6(self):
        return ":" in self.ip
    def check_connection(self)->ConnRes:
        url=self.make_download_url()
        try:
            res=requests.head(url,timeout=3)
            if res.status_code==200:
                self.latest_connection_result=PostFileForm.ConnRes.OK
                self.latest_connection_latency=res.elapsed.total_seconds()
                self.update_time = time.time()
                return PostFileForm.ConnRes.OK
            else: # this host is now closed, should switch to the other host
                self.latest_connection_latency = math.inf
                self.latest_connection_result = PostFileForm.ConnRes.FAIL
                self.update_time = time.time()
                return PostFileForm.ConnRes.FAIL
        except: # cannot access this url, but still have the chance to complete the transmission
            self.latest_connection_result = PostFileForm.ConnRes.UNKNOWN
            self.latest_connection_latency = res.elapsed.total_seconds()
            self.update_time = time.time()
            return PostFileForm.ConnRes.UNKNOWN

    def make_download_url(self,version="http")->str:
        url=version+"://["+self.ip+"]:"+str(self.port)+"/"+self.filename if self.is_ipv6() else version + "://" + self.ip + ":" + str(self.portcaptcha) + "/" + self.filename
        return url
    def contribute_ref(self):
        self.contribution+=1

    def have_hash(self)->bool:
        return (not (self.hash==None or self.hash==''))
    def append_hash(self,hash:str):
        self.hash = hash
        self.update_time = time.time()



