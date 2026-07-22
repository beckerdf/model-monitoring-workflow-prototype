# Outlook VBA Bridge — Setup Guide

Two macros run in Outlook on your Windows laptop. One saves matching
governance emails to the repo (inbound). One sends pending notifications
the Linux job has queued up (outbound).

---

## Before you start: enable macros

Outlook > File > Options > Trust Center > Trust Center Settings >
Macro Settings > **"Notifications for digitally signed macros, all other
macros disabled"** is fine — you'll just click "Enable" once when Outlook
starts, since these won't be signed. If that's too much friction, "Enable
all macros" works too (the warning is standard boilerplate, not specific
to this).

## Step 1 — Clone the repo locally on your Windows laptop

This is different from the JupyterLab clone — VBA needs a real local
folder it can write files into directly. Open **Git Bash** (not the
JupyterLab terminal):

```bash
cd ~/Documents
git clone https://github.com/dylanb_tmcc/model_monitoring_workflow.git prototype_model_monitoring
cd prototype_model_monitoring
git config credential.helper store
git pull
```

That last `git pull` will prompt for username/password once — use your
GitHub username and a **Personal Access Token** as the password (not your
real password; GitHub doesn't accept those anymore). Generate a token at
github.com → Settings → Developer settings → Personal access tokens →
Generate new token (classic) → check the `repo` scope. Once entered here,
`credential.helper store` saves it so you're never prompted again on this
machine.

**Note the full path** you cloned into (e.g.
`C:\Users\dylanb_adm\Documents\prototype_model_monitoring`) — both macros
below need it.

## Step 2 — Open the VBA editor

Outlook > Alt+F11 (or Developer tab > Visual Basic). In the Project
pane, find **Project1 > Microsoft Outlook Objects > ThisOutlookSession**,
double-click it, and paste in both macros below (one after another).

```vba
' ============================================================
' INBOUND: saves a matching governance email into the bridge,
' triggered by an Outlook Rule (set up in Step 3)
' ============================================================
Public Sub SaveGovernanceEmailToBridge(Item As Outlook.MailItem)
    On Error GoTo ErrHandler

    Dim repoPath As String
    Dim inboundPath As String
    Dim fileName As String
    Dim filePath As String
    Dim fileNum As Integer
    Dim cmd As String

    ' *** EDIT THIS to the exact path you cloned into in Step 1 ***
    repoPath = "C:\Users\dylanb_adm\Documents\prototype_model_monitoring"
    inboundPath = repoPath & "\bridge\inbound\"

    fileName = "email_" & Format(Now, "yyyymmdd_hhnnss") & ".txt"
    filePath = inboundPath & fileName

    fileNum = FreeFile
    Open filePath For Output As #fileNum
    Print #fileNum, Item.Body
    Close #fileNum

    cmd = "cmd.exe /c cd /d """ & repoPath & """ && git pull origin main --no-edit && git add bridge\inbound && git commit -m ""Inbound governance email"" && git push origin main"

    CreateObject("WScript.Shell").Run cmd, 0, True

    Exit Sub

ErrHandler:
    MsgBox "Bridge save failed: " & Err.Description
End Sub


' ============================================================
' OUTBOUND: checks for pending notifications and sends them,
' runs on a timer (started by Application_Startup below)
' ============================================================
Public Sub SendPendingBridgeNotifications()
    On Error GoTo ErrHandler

    Dim repoPath As String
    Dim outboundPath As String
    Dim cmd As String
    Dim fileName As String
    Dim filePath As String
    Dim fileNum As Integer
    Dim line As String
    Dim toAddr As String, ccAddr As String, subj As String, body As String
    Dim inBody As Boolean
    Dim mail As Outlook.MailItem

    ' *** EDIT THIS to match the same path as above ***
    repoPath = "C:\Users\dylanb_adm\Documents\prototype_model_monitoring"
    outboundPath = repoPath & "\bridge\outbound\"

    ' Pull first to pick up anything new the Linux job has queued
    cmd = "cmd.exe /c cd /d """ & repoPath & """ && git pull origin main --no-edit"
    CreateObject("WScript.Shell").Run cmd, 0, True

    fileName = Dir(outboundPath & "*.txt")
    Do While fileName <> ""
        filePath = outboundPath & fileName
        toAddr = "": ccAddr = "": subj = "": body = "": inBody = False

        fileNum = FreeFile
        Open filePath For Input As #fileNum
        Do While Not EOF(fileNum)
            Line Input #fileNum, line
            If Left(line, 4) = "TO: " Then
                toAddr = Mid(line, 5)
            ElseIf Left(line, 4) = "CC: " Then
                ccAddr = Mid(line, 5)
            ElseIf Left(line, 9) = "SUBJECT: " Then
                subj = Mid(line, 10)
            ElseIf line = "BODY_START" Then
                inBody = True
            ElseIf line = "BODY_END" Then
                inBody = False
            ElseIf inBody Then
                body = body & line & vbCrLf
            End If
        Loop
        Close #fileNum

        Set mail = Application.CreateItem(olMailItem)
        mail.To = Replace(toAddr, ";", "; ")
        If ccAddr <> "" Then mail.CC = Replace(ccAddr, ";", "; ")
        mail.Subject = subj
        mail.Body = body
        mail.Send

        Kill filePath
        fileName = Dir()
    Loop

    cmd = "cmd.exe /c cd /d """ & repoPath & """ && git add bridge\outbound && git commit -m ""Sent bridge notifications"" && git push origin main"
    CreateObject("WScript.Shell").Run cmd, 0, True

    Exit Sub

ErrHandler:
    MsgBox "Bridge send failed: " & Err.Description
End Sub


' ============================================================
' Runs SendPendingBridgeNotifications every 15 minutes while
' Outlook is open. Both macros only work while Outlook is running.
' ============================================================
Private Sub Application_Startup()
    ScheduleNextSend
End Sub

Public Sub ScheduleNextSend()
    Application.OnTime DateAdd("n", 15, Now), "SendPendingBridgeNotifications"
    Call SendPendingBridgeNotifications
End Sub
```

## Step 3 — Set up the inbound rule

Outlook > Rules > Manage Rules & Alerts > New Rule > "Apply rule on
messages I receive" > Next.

Condition: **From** → enter the Archer sender address
(`noreply@archerirm.us`) → Next.

Action: check **"run a script"** → click the link → select
`SaveGovernanceEmailToBridge` → Finish.

## Step 4 — Restart Outlook

The `Application_Startup` macro only fires on a fresh launch. Close and
reopen Outlook once after pasting the macros in. You should see a macro
security prompt — click **Enable**.

## Known limitations (say these out loud, don't wait to be asked)

- **Both directions only work while Outlook is open.** If you close it or
  your laptop sleeps, inbound emails still arrive (Outlook will catch up
  once reopened) but nothing gets sent or pulled until Outlook is running
  again.
- **No conflict handling.** If the Linux job and Outlook both try to push
  at the exact same moment, one push could fail. Rare in practice at this
  volume, but not impossible.
- **This is a bridge for the pilot, not the long-term design.** Once the
  Azure app registration exists (if it ever does), this whole file goes
  away and the original `graph_mailbox.py` / `notifications.py` come back
  into use — nothing else in the system changes.
