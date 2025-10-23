import jpype
import argparse

def hwpx_extract(hwpx_jar_path, file_path):

    ## jpype 시작
    jpype.startJVM(
        jpype.getDefaultJVMPath(),
        "-Djava.class.path={classpath}".format(classpath=hwpx_jar_path),
        convertStrings=True,
        )

    ## java package 가져오기

    HWPXFile = jpype.JClass('kr.dogfoot.hwpxlib.reader.HWPXReader')
    TextExtractor = jpype.JClass('kr.dogfoot.hwpxlib.tool.textextractor.TextExtractor')
    TextExtractMethod = jpype.JClass('kr.dogfoot.hwpxlib.tool.textextractor.TextExtractMethod')
    TextMarks = jpype.JClass('kr.dogfoot.hwpxlib.tool.textextractor.TextMarks')
    
    
    hwpx_file = HWPXFile.fromFilepath(file_path)
    text_extract_method = TextExtractMethod.AppendControlTextAfterParagraphText  
    text_marks = TextMarks()
    

    # 한글 추출
    hwpxtext = TextExtractor.extract(hwpx_file, text_extract_method, True, text_marks)

    return hwpxtext


if __name__=="__main__":
    
    # 파라미터 파싱    
    parser = argparse.ArgumentParser(description='Hwpx loader')
    parser.add_argument('--hwpx_jar_path', type=str, default='./hwpxlib-1.0.3.jar', help='hwpxlib jar 위치')
    parser.add_argument('--file_path', type=str, default='./test.hwpx', help='hwpx 파일 경로')
    args = parser.parse_args()

    hwp_text = hwpx_extract(args.hwpx_jar_path, args.file_path)
    
    # print로 표준출력
    print(hwp_text)