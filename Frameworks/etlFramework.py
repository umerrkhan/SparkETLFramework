import json, os, re, sys
from typing import Optional
from pyspark.sql import SparkSession
from pyspark.sql.dataframe import DataFrame
from pyspark.sql.types import StructType, StructField, IntegerType, StringType, LongType, ArrayType, DoubleType, \
    DateType, IntegerType


class ETL_Framework:
    def __init__(self, config):
        self.config = config

    def listofloadingfiles(self, location: str, pattern: Optional[str] = None) -> list:
        def FileOrDirectoy(location: str) -> str:
            if os.path.exists(location):
                if os.path.isfile(location):
                    return "File"
                else:
                    return "Dir"
            else:
                return "Invalid Path"

        def ListFiles(location: str) -> list:
            filelist = []
            for dirpath, dirname, filenames in os.walk(location):
                for filename in filenames:
                    filelist.append(f"{dirpath}/{filename}")
            return filelist

        def SearchSpecificfiles(filelist: list, pattern: Optional[str] = None) -> list:
            files = []
            if pattern == None:
                files = filelist
            else:
                for filename in filelist:
                    if re.search(rf"{pattern}", filename):
                        files.append(filename)
            return files

        if FileOrDirectoy(location) == "Dir":
            allfileslist = ListFiles(location)
            return SearchSpecificfiles(allfileslist, pattern)
        else:
            return SearchSpecificfiles(location)

    def getSparkSession(self, filepath: str, appDebug: Optional[str] = False) -> SparkSession:
        with open(filepath, "r") as f:
            SessionParams = json.load(f)

        Master = SessionParams["sparkconf"]["master"]
        AppName = SessionParams["sparkconf"]["appname"]
        LogLevel = SessionParams["log"]["level"]
        LogLevel = SessionParams.get('sparkconf', {}).get('log', "level")  # another method
        builder = SparkSession.builder.appName(AppName).master(Master)
        return builder.getOrCreate()

        if appDebug:
            print("Settings from Json File")
            print("Master    : ", Master)
            print("App Name  : ", AppName)
            print("Log Level :", LogLevel)
            print("Type :", type(SparkSession))
            print(SparkSession)
        return SparkSession

    def createDataFrame(self, sc: SparkSession, files: list, filetype: str, multiLine: Optional[str] = None,
                        FileStruct: Optional[StructType] = None) -> DataFrame:

        def createCSVDataFrame(sc: SparkSession, files: list) -> DataFrame:
            df = sc.read.format("csv") \
                .option("header", "true") \
                .option("mode", "DROPMALFORMED") \
                .load(files)
            return df

        def createJSONDataFrameJSON(sc: SparkSession, files: list, multiLine: str, FileStruct: StructType) -> DataFrame:
            print("json Function is called")
            print(multiLine)
            print(FileStruct)

            if multiLine == None and FileStruct == None:
                print("1- No Multiline and schema provided ")
                df = sc.read.format("json").option("mode", "PERMISSIVE").option("primitivesAsString", "true").load(
                    files)
            elif multiLine == "True" and FileStruct == None:
                print("2- Multiline is True but No Schema is provided")
                df = sc.read.format("json").option("mode", "PERMISSIVE").option("primitivesAsString", "true").option(
                    "multiline", "true").load(files)
            elif multiLine == "True" and FileStruct != None:
                print("3- Muliline is True and Schema is Provided")
                df = sc.read.option("mode", "FAILFAST").schema(FileStruct).json(files, multiLine=True)
            else:
                pass

            return df

        if filetype == "json":
            df = createJSONDataFrameJSON(sc, files, multiLine, FileStruct)

        elif filetype == "csv":
            df = createCSVDataFrame(sc, files)

        return df

    def showSampleDFValues(self, df: DataFrame):
        print("Printing Data Frame Schema")
        print(df.printSchema())
        print("Printing Top 10 Values of Data Frame")
        print(df.show(10))
        print("Total rows including mal format ", df.count())
