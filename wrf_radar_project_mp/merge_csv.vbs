Sub ImportCSVs()
'Author:    Jerry Beaucaire - Jingyin Tang
'Date:      8/16/2010
'Summary:   Import all CSV files from a folder into separate sheets
'           named for the CSV filenames
'Update:    2/8/2013   Macro replaces existing sheets if they already exist in master workbook
'Update:    6/7/2016   Added function to match sheets. Import csv from current folder'
Dim fPath   As String
Dim fCSV    As String
Dim wbCSV   As Workbook
Dim wbMST   As Workbook

Set wbMST = ThisWorkbook
fPath = Application.ActiveWorkbook.Path & "\"                  'path to CSV files, include the final
Application.ScreenUpdating = False  'speed up macro
Application.DisplayAlerts = False   'no error messages, take default answers
fCSV = Dir(fPath & "*.csv")         'start the CSV file listing

    On Error Resume Next
    Do While Len(fCSV) > 0
        Set wbCSV = Workbooks.Open(fPath & fCSV)                    'open a CSV file
        wbMST.Sheets(ActiveSheet.Name).Delete                       'delete sheet if it exists
        ActiveSheet.Move After:=wbMST.Sheets(wbMST.Sheets.Count)    'move new sheet into Mstr
        Columns.AutoFit             'clean up display
        fCSV = Dir                  'ready next CSV
    Loop
  
Application.ScreenUpdating = True
Set wbCSV = Nothing

End Sub

Sub FixRows()
'Now Let's match rows
Dim wbMST   As Workbook
Dim row1 As Integer
Dim row2 As Integer
Dim ws1 As Worksheet
Dim ws2 As Worksheet
Dim ws3 As Worksheet

Set wbMST = ThisWorkbook
Set ws1 = wbMST.Sheets(1)
Set ws2 = wbMST.Sheets(5)
Set ws3 = wbMST.Sheets(4)

For row1 = 2 To 50
    If StrComp(ws1.Cells(row1, 1), ws2.Cells(row1, 1)) < 0 Then
        ws2.Cells(row1, 1).EntireRow.Insert
        ws2.Cells(row1, 1).Value = ws1.Cells(row1, 1)
    End If
    If StrComp(ws1.Cells(row1, 1), ws3.Cells(row1, 1)) < 0 Then
        ws3.Cells(row1, 1).EntireRow.Insert
        ws3.Cells(row1, 1).Value = ws1.Cells(row1, 1)
    End If
Next row1


End Sub

Sub Relocate()
'Now Let's match rows
Dim wbMST   As Workbook

Set wbMST = ThisWorkbook
Set wsSource = wbMST.Sheets(6)

For Sheet = 1 To 5
    Set wsDest = wbMST.Sheets(Sheet)
    For Var = 0 To 3
        Set rangeSource = wsSource.Range(wsSource.Cells(1, Var * 5 + 1 + Sheet), wsSource.Cells(50, Var * 5 + 1 + Sheet))
        Set destSource = wsDest.Range(wsDest.Cells(1, 24 + Var), wsDest.Cells(50, 24 + Var))
        rangeSource.Copy destSource
    Next Var
Next Sheet

End Sub

Sub ChangeSeriesFormula()
    ''' Just do active chart
    If ActiveChart Is Nothing Then
        '' There is no active chart
        MsgBox "Please select a chart and try again.", vbExclamation, _
            "No Chart Selected"
        Exit Sub
    End If

    Dim OldString As String, NewString As String, strTemp As String
    Dim mySrs As Series

    OldString = InputBox("Enter the string to be replaced:", "Enter old string")

    If Len(OldString) > 1 Then
        NewString = InputBox("Enter the string to replace " & """" _
            & OldString & """:", "Enter new string")
        '' Loop through all series
        For Each mySrs In ActiveChart.SeriesCollection
            strTemp = WorksheetFunction.Substitute(mySrs.Formula, _
                OldString, NewString)
            mySrs.Formula = strTemp
        Next
    Else
        MsgBox "Nothing to be replaced.", vbInformation, "Nothing Entered"
    End If
End Sub


