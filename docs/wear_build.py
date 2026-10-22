from PIL import Image
import numpy as np,json,os,io,hashlib
S='/tmp/claude-0/-home-claude/e0b59010-292c-50e6-9078-47fd7e36bc66/scratchpad'
IN=S+'/outfit/inbox/';OUT='/home/claude/sanghanga-farm/a/wear/'
def f(n):
    for x in os.listdir(IN):
        if x.startswith(n+'_'):return IN+x
    return n
MW,MH=1024,510;SW,SH=1774,887
# 아이템: key, 이름, 칸, 45장 그림, 서기 그림
ITEMS=[('t_white','흰 티','top',f('13'),f('26')),('t_flannel','체크 남방','top',S+'/outfit/top_flannel.png',f('23')),('t_vest','작업 조끼','top',f('02'),f('03')),
('t_shirt','와이셔츠','top',f('08'),f('30')),('t_jeogori','한복 저고리','top',f('11'),f('35')),('t_panda','판다 티','top',f('37'),f('39')),
('b_overall','청멜빵','bot',f('12'),f('22')),('b_mombbae','꽃무늬 몸빼','bot',S+'/outfit/bot_mombbae.png',f('09')),('b_jeans','청바지','bot',f('07'),f('33')),
('b_suit','정장 바지','bot',f('28'),f('14')),('b_baji','한복 바지','bot',f('19'),f('31')),('b_panda','판다 바지','bot',f('36'),f('40')),
('h_straw','밀짚모자','hat',f('20'),f('25')),('h_cap','야구모자','hat',f('04'),f('29')),('h_beanie','털모자','hat',f('06'),f('10')),('h_towel','머릿수건','hat',f('32'),f('17')),
('h_bokgeon','복건','hat',f('34'),f('15')),('h_lincoln','링컨 모자','hat',f('24'),f('18')),('h_panda','판다 모자','hat',f('41'),f('38'))]
HM=json.load(open(S+'/hm.json'))
def load(p,W,H):
    a=np.array(Image.open(p).convert('RGB').resize((W,H),Image.LANCZOS)).astype(float)
    mag=(a[...,0]>160)&(a[...,2]>160)&(a[...,1]<130)&(np.abs(a[...,0]-a[...,2])<110)
    return a,~mag
# 프레임 위치표
def motion_ry():
    ry=np.full((MH,MW),-1.0)
    for D in HM.values():
        for F in D:
            for q in F:ry[q['y']:q['y']+q['h'],q['x']:q['x']+q['w']]=np.linspace(0,1,q['h'])[:,None]
    return ry
def stand_frames():
    from scipy import ndimage
    U=load(f('16'),SW,SH)[1]
    lab,n=ndimage.label(ndimage.binary_dilation(U,iterations=3))
    boxes=[]
    for s_ in ndimage.find_objects(lab):
        y0,y1,x0,x1=s_[0].start,s_[0].stop,s_[1].start,s_[1].stop
        if (y1-y0)*(x1-x0)>15000:
            e=int((y1-y0)*.14);boxes.append([max(0,x0-8),max(0,y0-e),x1-x0+16,y1-y0+e+4])
    big=sorted([b for b in boxes if b[3]>600],key=lambda b:b[0]);small=sorted([b for b in boxes if b[3]<=600],key=lambda b:(b[1]//250,b[0]))
    return big+small
SF=stand_frames();print('stand frames',len(SF),SF[:3])
def stand_ry():
    ry=np.full((SH,SW),-1.0)
    for x,y,w,h in SF:ry[y:y+h,x:x+w]=np.linspace(0,1,h)[:,None]
    return ry
def majority(m,ok,n=2):
    H,W=m.shape
    for _ in range(n):
        p=np.pad(m,1);c=sum(p[1+dy:H+1+dy,1+dx:W+1+dx] for dy in(-1,0,1) for dx in(-1,0,1));m=(c>=5)&ok
    return m
def sat(a):
    mx=a.max(-1);mn=a.min(-1);return np.where(mx>0,(mx-mn)/np.maximum(mx,1),0)
def isskin(a):
    r,g,b=a[...,0],a[...,1],a[...,2];return (r>g)&(g>b)&(r-b>45)&(r>150)&(sat(a)<.58)
RNG={'top':(.30,.74),'bot':(.48,.9),'b_overall':(.31,.9),'hat':(-1,.62)}
CUT=.37
def save(arr,mask,path):
    o=np.zeros(arr.shape[:2]+(4,),np.uint8);o[...,:3]=arr.clip(0,255).astype(np.uint8);o[...,3]=mask*255
    im=Image.fromarray(o)
    if arr.shape[1]==SW:im=im.resize((SW//2,SH//2),Image.LANCZOS)
    im.save(path,'WEBP',quality=90,method=6)
def frames_of(kind):
    if kind=='m':return [(q['x'],q['y'],q['w'],q['h']) for D in HM.values() for F in D for q in F]
    return [tuple(b) for b in SF]
def align(A,ma,Bm,kind):
    R=np.zeros_like(A);Rm=np.zeros_like(ma);H,W=ma.shape;M=6 if kind=='m' else 10
    for x,y,w,h in frames_of(kind):
        x0,y0,x1,y1=max(0,x-M),max(0,y-M),min(W,x+w+M),min(H,y+h+M)
        best=(-1,0,0);bm=Bm[y:y+h,x:x+w]
        for dy in range(-M,M+1):
            for dx in range(-M,M+1):
                ys,xs=y+dy,x+dx
                if ys<0 or xs<0 or ys+h>H or xs+w>W:continue
                im=ma[ys:ys+h,xs:xs+w];sc=(im&bm).sum()/max(1,(im|bm).sum())
                if sc>best[0]:best=(sc,dx,dy)
        _,dx,dy=best
        R[y:y+h,x:x+w]=A[y+dy:y+dy+h,x+dx:x+dx+w];Rm[y:y+h,x:x+w]=ma[y+dy:y+dy+h,x+dx:x+dx+w]
    return R,Rm
def build(kind,W,H,ry,bases,basekey):
    os.makedirs(OUT+kind,exist_ok=True)
    B={k:load(p,W,H) for k,p in bases.items()}
    nb,nm=B[basekey]
    save(nb,nm&(ry>=CUT),OUT+kind+'/base_body.webp');save(nb,nm&(ry<CUT)&(ry>=0),OUT+kind+'/base_head.webp')
    for key,name,slot,pm,ps in ITEMS:
        p=pm if kind=='m' else ps
        A,ma=load(p,W,H);A,ma=align(A,ma,B[basekey][1],kind)
        lo,hi=RNG.get(key,RNG[slot])
        inr=(ry>=lo)&(ry<hi)
        if slot=='hat':
            Bb,mb=B[basekey];d=np.sqrt(((A-Bb)**2).sum(-1))
            m=ma&(((ry<CUT)&(ry>=0))|(inr&(d>50)&~isskin(A)))
        else:
            best=None
            for k,(Bb,mb) in B.items():
                d=np.sqrt(((A-Bb)**2).sum(-1));sc=(d*(inr&ma)).sum()
                if best is None or sc<best[0]:best=(sc,k,d)
            d=best[2];m=ma&inr&(d>45)&~isskin(A)
            if slot=='bot':
                s=sat(A);m&=~((s<.12)&(A.mean(-1)>150)&(ry<.6))
        m=majority(m,ma)
        save(A,m,OUT+kind+'/'+key+'.webp')
    print(kind,'done')
build('m',MW,MH,motion_ry(),{'g':S+'/outfit/base.png','n':f('27')},'n')
build('s',SW,SH,stand_ry(),{'a':f('01'),'b':f('25'),'n':f('16')},'n')
json.dump({'items':[[k,n,s] for k,n,s,_,_ in ITEMS],'sf':[[x//2,y//2,w//2,h//2] for x,y,w,h in SF]},open(OUT+'wear.json','w'),ensure_ascii=False)
