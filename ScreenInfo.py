# 屏幕尺寸相关信息

template_screenInfo = {
    "midSize":{
        "position":[0,0],
        "pointNum":[32,16],
        "pointSize":4,
        "scale":(6,6),
    },
    "midSizeScaled68":{
        "position":[0,0],
        "pointNum":[32,16],
        "pointSize":4,
        "scale":(6,8),
    },
    "midSizeScaled":{
        "position":[0,0],
        "pointNum":[32,16],
        "pointSize":4,
        "scale":(6,9),
    },
    "bigSize":{
        "position":[0,0],
        "pointNum":[32,16],
        "pointSize":6,
        "scale":(8,8),
    },
    "bigSizeScaled810":{
        "position":[0,0],
        "pointNum":[32,16],
        "pointSize":6,
        "scale":(8,10),
    },
    "bigSizeScaled":{
        "position":[0,0],
        "pointNum":[32,16],
        "pointSize":6,
        "scale":(8,12),
    },
    "bigSizeScaled910":{
        "position":[0,0],
        "pointNum":[32,16],
        "pointSize":7,
        "scale":(9,10),
    },
    "bigSize1212":{
        "position":[0,0],
        "pointNum":[32,16],
        "pointSize":9,
        "scale":(12,12),
    },
    "smallSize":{
        "position":[0,0],
        "pointNum":[32,16],
        "pointSize":3,
        "scale":(4,4),
    },
    "smallSizeScaled":{
        "position":[0,0],
        "pointNum":[32,16],
        "pointSize":3,
        "scale":(4,6),
    },
    "miniSize":{
        "position":[0,0],
        "pointNum":[32,16],
        "pointSize":2,
        "scale":(3,3),
    },
}

pointKindDict = {}

for key,value in template_screenInfo.items():
	pointKindDict[str(value["scale"]).replace(" ","")] = key


template_monochromeColors = {
    "white":((60,60,60),(255,255,255)),
    "red":((80,60,60),(255,90,90)),
    "yellow":((80,80,60),(255,255,40)),
    "green":((60,80,60),(40,255,40)),
    "orange":((80,80,60),(255,220,40)),
    "kelly":((80,80,60),(200,255,40)),
    "red_2":((60,60,60),(255,90,90)),
    "yellow_2":((60,60,60),(255,255,40)),
    "green_2":((60,60,60),(40,255,40)),
    "orange_2":((60,60,60),(255,220,40)),
    "kelly_2":((60,60,60),(200,255,40)),
    
}