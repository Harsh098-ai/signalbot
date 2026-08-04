# Setup Guide (no coding needed)

You will not touch a terminal or install anything. Everything below happens in a web browser.

Total time: about 30 minutes, once. After that it runs by itself every weekday morning.

There are three parts:
- **Part A** — put the bot's files online (10 min)
- **Part B** — create a special email password (10 min)
- **Part C** — switch it on and test (10 min)

Do them in order.

---

## Part A: Put the files online

We use GitHub. Think of it as Google Drive that can also run programs on a schedule. It is free.

### A1. Make an account
Go to **github.com** and sign up. Any email works. Verify the email they send you.

### A2. Create a place for the files
1. Click the **+** icon in the top right corner of the page
2. Click **New repository**
3. Repository name: type `signalbot`
4. Select **Private** (important, this keeps it hidden from everyone else)
5. Click **Create repository**

### A3. Upload the files
You will see a mostly empty page with some setup text.

1. Find the link that says **uploading an existing file** and click it
   (if you cannot see it, add `/upload/main` to the end of the page address)
2. Download **signalbot.zip** and unzip it. On Mac just double click it. On Windows, right click and choose **Extract All**.
3. Open the `signalbot` folder that appears. Select **everything inside it** and drag it all into the browser window.
   Do not drag the `signalbot` folder itself, drag the files that are inside it.
4. **Important:** there is a hidden folder called `.github` in there. On Mac press `Cmd + Shift + .` to show hidden folders. On Windows, open File Explorer, click **View**, then tick **Hidden items**. Drag that `.github` folder in too.
5. Scroll to the bottom and click the green **Commit changes** button

When it finishes you should see a file list including `main.py`, `config.py`, `README.md` and others.

### A4. Check the hidden folder made it
Look at your file list. You should see a folder named `.github`. Click into it, then into `workflows`. There should be a file called `daily.yml`.

**If `.github` is not there, the bot will never run.** Go back to step A3 and try again with hidden files showing.

---

## Part B: Create the email password

Gmail will not let a program use your normal password. You need a separate one just for this. It is called an App Password.

### B1. Turn on 2-Step Verification
This is required before app passwords become available.

1. Go to **myaccount.google.com**
2. Click **Security** in the left menu
3. Find **2-Step Verification** and turn it on
4. Follow the prompts (it will send a code to your phone)

If you already have this on, skip to B2.

### B2. Generate the app password
1. Still in Security, search the page for **App passwords**
   (or go straight to **myaccount.google.com/apppasswords**)
2. In the name box type `signalbot`
3. Click **Create**
4. A **16 character password** appears in a yellow box, something like `abcd efgh ijkl mnop`

**Copy it now and paste it somewhere safe.** Google shows it once and never again. If you lose it, just delete that entry and make a new one.

You can ignore the spaces when you use it later.

---

## Part C: Switch it on

### C1. Store your credentials safely
Back on your GitHub repository page:

1. Click **Settings** (in the row of tabs at the top: Code, Issues, Pull requests... Settings is at the far right)
2. In the left menu click **Secrets and variables**, then **Actions**
3. Click the green **New repository secret** button

Add the first one:
- Name: `SMTP_USER`
- Secret: your full Gmail address, for example `harsh@gmail.com`
- Click **Add secret**

Click **New repository secret** again and add the second:
- Name: `SMTP_PASS`
- Secret: the 16 character app password from Part B
- Click **Add secret**

The names must be typed exactly as shown, all capitals with the underscore. You should now see two secrets listed.

You do not need a third one. The recipient address is already built in.

### C2. Allow it to run
1. Click the **Actions** tab at the top of your repository
2. If you see a green button saying **I understand my workflows, go ahead and enable them**, click it
3. On the left you should now see **Daily account signals**

### C3. Test it right now
1. Click **Daily account signals** in the left menu
2. On the right, click the **Run workflow** dropdown
3. Click the green **Run workflow** button

Wait about 30 seconds, then refresh the page. A new run appears with a spinning yellow dot. It takes roughly 3 to 8 minutes.

- **Yellow dot** = still working, wait
- **Green tick** = it worked, check the inbox
- **Red cross** = something went wrong, see Troubleshooting below

### C4. Check the email
Look in the recipient inbox. **Also check the spam folder**, because the very first one often lands there. If it does, open it and mark it **Not spam** so future ones arrive properly.

---

## What happens now

It runs automatically at 8am India time, Monday to Friday. You do nothing.

**Your first email will be big and noisy.** Every company looks brand new to the bot on day one, so it flags a lot. This is normal and it settles down from the second run onward, when it only reacts to genuine changes.

---

## Troubleshooting

**Red cross on the run**
Click the failed run, then click the box that says `digest`, and look for a line in red. Send me that line and I will tell you what to fix.

**"Authentication failed" or "Username and Password not accepted"**
The app password is wrong. Most likely causes: you used your normal Gmail password instead of the 16 character one, or you typed the secret name slightly differently. Redo step C1.

**Green tick but no email arrived**
Check spam first. If it is not there, the run probably found nothing above the score threshold, which happens on quiet news days. Click into the run and read the output, it says how many accounts cleared the bar.

**Nothing under the Actions tab at all**
The `.github` folder did not upload. Redo step A3 with hidden files visible.

---

## Changing things later

You can edit any file straight in the browser. Click the file, click the pencil icon, make your change, click **Commit changes**.

The things you are most likely to want to change all live in `config.py`:

- `EMAIL_TO` — who receives it
- `MIN_SCORE_TO_REPORT` — currently 30. Raise it to 50 if you get too many accounts, drop it to 20 if you get too few.
- `FUNDING_FEEDS` — the news sources it watches

And in `.github/workflows/daily.yml`, the line `cron: '30 2 * * 1-5'` controls timing. That is 8am India time. To make it 9am, change `30 2` to `30 3`.

---

## A shortcut worth considering

If any of the above gets frustrating, this is a genuinely small job for someone technical. A sales engineer or anyone on an engineering team could do the whole thing in about fifteen minutes. Send them the folder and this guide, and the only thing you need to handle personally is the Gmail app password in Part B, since that is tied to your own account.

Not a failure to ask. It is just faster.
