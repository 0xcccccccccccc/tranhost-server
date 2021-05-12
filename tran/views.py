import datetime as datetime
from django.http import HttpResponse,JsonResponse
from django.shortcuts import render, redirect
from django.core.cache import cache
from django_redis import get_redis_connection
from tran.chinese_dict import data
from django.views.decorators.csrf import csrf_exempt
import random
import time
import hashlib


default = get_redis_connection('default')

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

def index(request):
    return render(request,"index.html")

@csrf_exempt
def postfile(request):
    if request.method=="POST":
        ip=request.POST["ip"]
        port=request.POST["port"]
        filename=request.POST["filename"]
        captcha = request.POST["captcha"]
        password=request.POST.get("password",None)
        if hashlib.md5((ip + port + filename + captcha).encode("utf8")).hexdigest().startswith("000"):
            uuid = get_a_friendly_uuid(ip+port+filename)
            cache.set(uuid,{"port":port,"filename":filename,"ip":ip,"password":password})
            return HttpResponse(uuid)
        else:
            return HttpResponse("内部错误")
def getfile(request):
    uuid=request.path
    obj=cache.get(uuid,None)
    if(obj!=None):
        if(obj["password"]==None or obj["password"]==''):
            return redirect(to="http://[%s]:%s/%s" % (
            obj["ip"], obj["port"], obj["filename"]))
            # return render(request, "start_download.html", {"filename": obj["filename"], "url": "http://[%s]:%s/%s" % (
            # obj["ip"], obj["port"], obj["filename"])})

        else:
            password=request.POST.get("password",None)
            captcha_question=request.session.get("captcha",None)
            captcha_anwser=request.POST.get("captcha",None)
            if password==None:
                request.session["captcha"]=get_a_fridenly_word()
                return render(request,"password_required.html",{"title":"请输入提取密码来提取","filename":obj["filename"],"question":request.session["captcha"]})
            elif password==obj["password"] and (hashlib.md5((str(captcha_question)+str(captcha_anwser)).encode("utf8")).hexdigest().startswith("000")):
                return redirect(to="http://[%s]:%s/%s" % (
                    obj["ip"], obj["port"], obj["filename"]))
                #return render(request,"start_download.html",{"filename":obj["filename"],"url":"http://[%s]:%s/%s"%(obj["ip"], obj["port"], obj["filename"])})
            else:
                return render(request,"password_required.html",{"title":"密码错误，重新输入来提取","filename":obj["filename"]})

    else:
        return HttpResponse(status=404)
