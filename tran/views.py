from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.core.cache import cache
from django.views.decorators.csrf import csrf_exempt
import random
from tran.models import PostFileForm
from tran.task_latency_test import TaskLatencyTest

def index(request):
    return render(request,"index.html")
@csrf_exempt
def appendhash(request):
    if request.method=="POST":
        uuid=request.POST["uuid"]
        hashval=request.POST["hash"]
        cacheobj:PostFileForm=cache.get(uuid, None)
        cache.set(uuid,cacheobj.append_hash(hashval))
        if cache.get("hashset",None)==None:
            cache["hashset"]={hashval:[cacheobj.append_hash(hashval)]}
            return HttpResponse("OK",status=200)
        else:
            if cache["hashset"].get(hashval,None)==None:
                cache["hashset"][hashval]=[cacheobj.append_hash(hashval)]
                return HttpResponse("OK", status=200)
            else:
                cache["hashset"][hashval].append(cacheobj.append_hash(hashval))
                return HttpResponse("OK", status=200)
@csrf_exempt
def postfile(request):
    if request.method=="POST":
        form=PostFileForm(request)
        if form.validate_captcha():
            uuid = form.get_a_friendly_uuid()
            # cache.set(uuid,{"port":str(form.port),"filename":form.filename,"ip":form.ip,"password":form.password})
            cache.set(uuid,form)
            return HttpResponse(uuid)
        else:
            return HttpResponse("内部错误")

@csrf_exempt
def getcaptcha(request):
    request.session["captcha"] = hex(hex(random.randint(0, 0xffffffff)).__hash__())
    return HttpResponse(request.session["captcha"],status=200)
def tryMakeFileResponse(cacheobj:PostFileForm):
    if not cacheobj.check_connection() == PostFileForm.ConnRes.FAIL:
        return redirect(to=cacheobj.make_download_url())
    else:
        try:
            cacheobjs: list = cache["hashset"][cacheobj.hash]
            cacheobjs = sorted(cacheobjs, key=lambda x: x.latest_connection_latency)[:10]
            url = cacheobjs[0].make_download_url()
            cacheobjs[0].contribute_ref()
            TaskLatencyTest(cacheobjs)  # test latency again
            return redirect(to=url)
        except:
            return redirect(to=cacheobj.make_download_url())
@csrf_exempt
def getfile(request):
    uuid=request.path
    cacheobj:PostFileForm= cache.get(uuid,None)
    if(cacheobj!=None): # valid file
        if not cacheobj.have_password():
            return tryMakeFileResponse(cacheobj)
        else:
            validate_result=cacheobj.validate_password(request)
            if validate_result==PostFileForm.PwdValidRes.CORRECT:
                if not cacheobj.check_connection() == PostFileForm.ConnRes.FAIL:
                    return tryMakeFileResponse(cacheobj)
            elif validate_result==PostFileForm.PwdValidRes.INVALID_FORM: # password needed
                request.session["captcha"] = hex(hex(random.randint(0, 0xffffffff)).__hash__())
                return render(request, "password_required.html",
                              {"title": "请输入提取密码来提取", "filename": cacheobj.filename,
                               "question": request.session["captcha"]}, status=401)
            elif validate_result==PostFileForm.PwdValidRes.WRONG_PASSWORD or validate_result==PostFileForm.PwdValidRes.WRONG_CAPTCHA:
                request.session["captcha"] = hex(hex(random.randint(0, 0xffffffff)).__hash__())
                return render(request, "password_required.html",
                              {"title": "密码错误，重新输入来提取", "filename": cacheobj.filename,
                               "question": request.session["captcha"]}, status=401)
    else:
        return HttpResponse(status=404)
