from ScreenInfo import *

template_busLine_custom = {
    "lineName":"testLine1",
    "preset":"自定义",
    "flushRate":50,
    "programSheet":[],
    "frontScreen":{
        "enabled":True,
        "colorMode":"RGB",    # "RGB","1"
        "screenSize":[224,32,(6,6)],
        "layout":"",
        "screenUnit":[
            {
                "position":[0,0],
                "pointNum":[224,32],
                "pointSize":4,
                "scale":(6,6),
                # "color":(80,40,40),
                # "color":(255,40,40)
                }
        ],
        # "subProgramSheet":[]
    },
    "backScreen":{
        "enabled":False,
        "colorMode":"RGB",    # "RGB","1"
        "screenSize":[224,32,(6,6)],
        "layout":"",
        "screenUnit":[
            {
                "position":[0,0],
                "pointNum":[224,32],
                "pointSize":4,
                "scale":(6,6),
                # "color":(80,40,40),
                # "color":(255,40,40)
                }
        ],
        # "subProgramSheet":[]
    },
    "frontSideScreen":{
        "enabled":True,
        "colorMode":"RGB",    # "RGB","1"
        "screenSize":[224,32,(6,6)],
        "layout":"",
        "screenUnit":[
            {
                "position":[0,0],
                "pointNum":[224,32],
                "pointSize":4,
                "scale":(6,6),
                # "color":(80,40,40),
                # "color":(255,40,40)
                }
        ],
        # "subProgramSheet":[]
    },
    "backSideScreen":{
        "enabled":False,
        "colorMode":"RGB",    # "RGB","1"
        "screenSize":[224,32,(6,6)],
        "layout":"",
        "screenUnit":[
            {
                "position":[0,0],
                "pointNum":[224,32],
                "pointSize":4,
                "scale":(6,6),
                # "color":(80,40,40),
                # "color":(255,40,40)
                }
        ],
        # "subProgramSheet":[]
    }
}

template_busLine_bjbus = {
    "lineName":"testLine1",
    "preset":"北京公交",
    "flushRate":50,
    "programSheet":[],
    "frontScreen":{
        "enabled":True,
        "colorMode":"1",    # "RGB","1"
        "screenSize":[224,32,(6,6)],
        "layout":"布局1",
        "screenUnit":[
            {
                "position":[0,0],
                "pointNum":[80,32],
                "pointSize":4,
                "scale":(6,6),
                # "color":(80,80,40),
                # "color":(255,255,40)
                },
            {
                "position":(80*6,0),
                "pointNum":[48,16],
                "pointSize":6,
                "scale":(8,12),
                # "color":(80,40,40),
                # "color":(255,40,40)
                },
            {
                "position":(80*6+48*8,0),
                "pointNum":[80,32],
                "pointSize":4,
                "scale":(6,6),
                # "color":(80,80,40),
                # "color":(255,255,40)
                },
        ],
        # "subProgramSheet":[]
    },
    "backScreen":{
        "enabled":False,
        "colorMode":"1",    # "RGB","1"
        "screenSize":[224,32,(6,6)],
        "layout":"布局1",
        "screenUnit":[
           {
                "position":[0,0],
                "pointNum":[80,32],
                "pointSize":4,
                "scale":(6,6),
                # "color":(80,80,40),
                # "color":(255,255,40)
                },
            {
                "position":(80*6,0),
                "pointNum":[48,16],
                "pointSize":6,
                "scale":(8,12),
                # "color":(80,40,40),
                # "color":(255,40,40)
                },
            {
                "position":(80*6+48*8,0),
                "pointNum":[80,32],
                "pointSize":4,
                "scale":(6,6),
                # "color":(80,80,40),
                # "color":(255,255,40)
                },
        ],
        # "subProgramSheet":[]
    },
    "frontSideScreen":{
        "enabled":True,
        "colorMode":"1",    # "RGB","1"
        "screenSize":[128,16,(8,8)],
        "layout":"布局5",
        "screenUnit":[
            {
                "position":[0,0],
                "pointNum":[48,16],
                "pointSize":6,
                "scale":(8,8),
                # "color":(80,40,40),
                # "color":(255,40,40)
                },
            {
                "position":(48*8,0),
                "pointNum":[80,16],
                "pointSize":6,
                "scale":(8,8),
                # "color":(80,80,40),
                # "color":(255,255,40)
                },
        ],
        # "subProgramSheet":[]
    },
    "backSideScreen":{
        "enabled":False,
        "colorMode":"1",    # "RGB","1"
        "screenSize":[128,16,(8,8)],
        "layout":"布局5",
        "screenUnit":[
            {
                "position":[0,0],
                "pointNum":[48,16],
                "pointSize":6,
                "scale":(8,8),
                # "color":(80,40,40),
                # "color":(255,40,40)
                },
            {
                "position":(48*8,0),
                "pointNum":[80,16],
                "pointSize":6,
                "scale":(8,8),
                # "color":(80,80,40),
                # "color":(255,255,40)
                },
        ],
        # "subProgramSheet":[]
    }
}

template_busLine_common = {
    "lineName":"testLine1",
    "preset":"普通",
    "flushRate":50,
    "programSheet":[],
    "frontScreen":{
        "enabled":True,
        "colorMode":"1",    # "RGB","1"
        "screenSize":[160,24,(6,6)],
        "layout":"布局1",
        "screenUnit":[
            {
                "position":[0,0],
                "pointNum":[64,24],
                "pointSize":4,
                "scale":(6,6),
                # "color":(80,80,40),
                # "color":(255,255,40)
                },
            {
                "position":(64*6,0),
                "pointNum":[32,24],
                "pointSize":4,
                "scale":(6,6),
                # "color":(80,40,40),
                # "color":(255,40,40)
                },
            {
                "position":(64*6+32*6,0),
                "pointNum":[64,24],
                "pointSize":4,
                "scale":(6,6),
                # "color":(80,80,40),
                # "color":(255,255,40)
                },
        ],
        # "subProgramSheet":[]
    },
    "backScreen":{
        "enabled":False,
        "colorMode":"1",    # "RGB","1"
        "screenSize":[160,24,(6,6)],
        "layout":"布局1",
        "screenUnit":[
            {
                "position":[0,0],
                "pointNum":[64,24],
                "pointSize":4,
                "scale":(6,6),
                # "color":(80,80,40),
                # "color":(255,255,40)
                },
            {
                "position":(64*6,0),
                "pointNum":[32,24],
                "pointSize":4,
                "scale":(6,6),
                # "color":(80,40,40),
                # "color":(255,40,40)
                },
            {
                "position":(64*6+32*6,0),
                "pointNum":[64,24],
                "pointSize":4,
                "scale":(6,6),
                # "color":(80,80,40),
                # "color":(255,255,40)
                },
        ],
        # "subProgramSheet":[]
    },
    "frontSideScreen":{
        "enabled":True,
        "colorMode":"1",    # "RGB","1"
        "screenSize":[128,16,(8,8)],
        "layout":"布局5",
        "screenUnit":[
            {
                "position":[0,0],
                "pointNum":[48,16],
                "pointSize":6,
                "scale":(8,8),
                # "color":(80,40,40),
                # "color":(255,40,40)
                },
            {
                "position":(48*8,0),
                "pointNum":[80,16],
                "pointSize":6,
                "scale":(8,8),
                # "color":(80,80,40),
                # "color":(255,255,40)
                },
        ],
        # "subProgramSheet":[]
    },
    "backSideScreen":{
        "enabled":False,
        "colorMode":"1",    # "RGB","1"
        "screenSize":[128,16,(8,8)],
        "layout":"布局5",
        "screenUnit":[
            {
                "position":[0,0],
                "pointNum":[48,16],
                "pointSize":6,
                "scale":(8,8),
                # "color":(80,40,40),
                # "color":(255,40,40)
                },
            {
                "position":(48*8,0),
                "pointNum":[80,16],
                "pointSize":6,
                "scale":(8,8),
                # "color":(80,80,40),
                # "color":(255,255,40)
                },
        ],
        # "subProgramSheet":[]
    }
}

template_station = {
    "stationName":"testLine1",
    "remark":"",
    "flushRate":50,
    "programSheet":[],
    "Screen":{
        "enabled":True,
        "colorMode":"RGB",    # "RGB","1"
        "screenSize":[144,16,(8,8)],
        "layout":"",
        "screenUnit":[
            {
                "position":[0,0],
                "pointNum":[144,16],
                "pointSize":6,
                "scale":(8,8),
                # "color":(80,40,40),
                # "color":(255,40,40)
                }
        ],
        # "subProgramSheet":[]
    }
}

template_program_show = {
        "font":"宋体",
        "fontSize":16,
        "ascFont":"ASC1608",
        "ascFontSize":16,
        "sysFontOnly":False,
        "rollAscii":False,
        "appearance":"静止",
        "vertical":False,
        "argv_1":1,
        "argv_2":1,
        "argv_3":1,
        "spacing":0,
        "bold":[1,1],
        "y_offset":0,
        "y_offset_asc":0,
        "x_offset":0,
        "y_offset_global":0,
        "align":[0,0], # x对齐，y对齐
        "scale":100,
        "autoScale":False,
        "scaleSysFontOnly":False,
        "multiLine":False,
        "lineSpace":1,
        "richText":[False,False],
        "text":"",
        "color_1":"white",
        "color_RGB":[255,255,255],
        "bitmap":None,    # bitmap是BmpCreater生成的图像对象
}

template_sub_program = [    # 节目单中的一个节目应该包含所有屏幕的显示内容，每个屏幕有分区，这是每个节目的子节目，即每个屏幕要显示的内容
    template_program_show,
    # screen1,screen2,....
]

template_program = ["默认节目",60]

template_programSheet = [template_program]

if __name__ == "__main__":
    print(template_programSheet)