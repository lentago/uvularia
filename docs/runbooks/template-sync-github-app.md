# Let uvularia update its three template repositories by itself

**What you're about to do:** create one small GitHub App, which is GitHub's way
of giving a workflow its own identity and its own narrow set of keys, install it
on exactly the three "Use this template" repositories, and hand its id and its
private key to this repository. From then on, every merge here that changes a
template opens a pull request on the matching template repository on its own.

**Why bother:** the three template repositories
([records](https://github.com/lentago/uvularia-records-template),
[rules](https://github.com/lentago/uvularia-rules-template),
[site](https://github.com/lentago/uvularia-site-template)) are copies of
`templates/records`, `templates/ask-rules` and `templates/site` in this repo. A
"Use this template" button needs a whole repository, so the copies have to
exist. Until this App exists, someone has to copy the changes across by hand
after every merge, and the copies drift. The
[template-sync workflow](../../.github/workflows/template-sync.yml) already
checks for that drift on every pull request; this is what lets it fix the drift
instead of just reporting it.

**You'll need:** to be an owner of the `lentago` GitHub organization. Nothing
else. No command line.

**Time:** about ten minutes.

**Skip this if** you are happy to keep syncing by hand. The drift check will keep
telling you when a sync is due, and the by-hand recipe is at the bottom.

---

## Heads up, before you start

- GitHub shows you the App's **private key exactly once**, as a file download.
  Treat it like a password: it goes into one GitHub secret and nowhere else, and
  you delete the downloaded file when you're done. If it ever leaks, the fix is
  easy (see *Undo* below), and the worst it can do is open pull requests on the
  three template repositories. It cannot merge anything, because their checks
  still gate every merge.
- Nothing you do here touches the template repositories' content. Installing an
  App only grants permission; the first real change still arrives as a pull
  request you can read.

## 1. Create the App

1. Sign in to GitHub. Click your profile picture, top right, then **Your
   organizations**, then **lentago**.
2. Click the organization's **Settings** tab.
3. In the left sidebar, scroll to the very bottom and click **Developer
   settings**, then **GitHub Apps**, then the green **New GitHub App** button.
4. Fill in the form. Leave everything you don't see here at its default:

   | Field | Put |
   |---|---|
   | **GitHub App name** | `lentago-template-sync` |
   | **Homepage URL** | `https://github.com/lentago/uvularia` |
   | **Webhook → Active** | **untick** it. This App never needs to be called by GitHub; it only needs permission to act. |
   | **Repository permissions → Contents** | **Read and write** (it pushes a branch) |
   | **Repository permissions → Pull requests** | **Read and write** (it opens the pull request and arms auto-merge) |
   | **Repository permissions → Workflows** | **Read and write** (the templates contain workflow files, and GitHub refuses to push those without this) |
   | **Repository permissions → Metadata** | Read-only. GitHub sets this one itself. |
   | **Where can this GitHub App be installed?** | **Only on this account** |

5. Click **Create GitHub App**. You land on the App's settings page.

## 2. Write down the App ID and get the key

1. Near the top of the App's settings page is **App ID**, a number like
   `1234567`. Copy it somewhere handy; you'll paste it in step 4.
2. Scroll down to **Private keys** and click **Generate a private key**. Your
   browser downloads a file ending in `.pem`. That file *is* the key. Leave it
   in your downloads folder for a few minutes; you'll paste its contents in
   step 4 and then delete it.

## 3. Install the App on the three template repositories only

1. In the App's settings page, left sidebar, click **Install App**.
2. Next to **lentago**, click **Install**.
3. Choose **Only select repositories**, open the dropdown, and tick exactly
   these three:
   - `uvularia-records-template`
   - `uvularia-rules-template`
   - `uvularia-site-template`
4. Click **Install**.

**Heads up:** do not pick *All repositories*. The whole point of an App over a
personal token is that this key can reach these three repositories and nothing
else.

## 4. Give this repository the id and the key

1. Open <https://github.com/lentago/uvularia/settings/secrets/actions>. (That
   is this repository → **Settings** → **Secrets and variables** → **Actions**.)
2. Click the **Variables** tab, then **New repository variable**:
   - Name: `TEMPLATE_SYNC_APP_ID`
   - Value: the App ID number from step 2.
   Click **Add variable**.
3. Click the **Secrets** tab, then **New repository secret**:
   - Name: `TEMPLATE_SYNC_APP_PRIVATE_KEY`
   - Secret: open the downloaded `.pem` file in any text editor, select
     everything, and paste it here. Include the `-----BEGIN RSA PRIVATE KEY-----`
     and `-----END RSA PRIVATE KEY-----` lines; they are part of the key.
   Click **Add secret**.
4. Delete the `.pem` file from your downloads folder, and empty the trash.

## 5. Run it once by hand

1. Open <https://github.com/lentago/uvularia/actions/workflows/template-sync.yml>.
2. Click **Run workflow**, keep `main`, click the green **Run workflow** button.
3. Wait a minute and open the run.

## How you know it worked

- The run shows one **drift** job and three **sync** jobs, all green.
- Each **sync** job either says `already matches` (nothing to do; the templates
  were in step) or ends with a link to a new pull request on that template
  repository, opened by **lentago-template-sync[bot]**, with auto-merge armed.
  Open one: the diff is only the files that differ from this repo's subtree.
- Within a few minutes those pull requests merge on their own once their checks
  pass, and the next **drift** job reports `ok` for all three.

If instead a **sync** job prints a notice that the App is not configured, one of
the two names in step 4 is misspelled, or the secret is empty. Fix it and run
again. If it fails while minting a token, the App is created but not installed
on that repository (step 3).

## If auto-merge is refused

The first live run opened its pull request and then stopped with
`User is not authorized for this protected branch (enablePullRequestAutoMerge)`.
That means the template repository's branch protection does not yet let the App
press the "merge when green" button. The pull request is fine; arm it by hand
this once, then fix the setting so the next run needs nobody:

- **If the template repositories' settings are managed as code** (in Lentago's
  case they are, by `lentago/.github`'s Terraform), add the App to the push
  allowlist for the three template repositories (`gate_extra_allowances` in
  `terraform/locals.tf`, by the App's `A_…` node id) and let the apply carry it.
- **Otherwise**, in each template repository: **Settings → Branches →** the
  rule on `main` **→ Restrict who can push to matching branches → add
  `lentago-template-sync`** (it appears under *Apps* once installed). Save.
  Repeat for the other two.

**Heads up:** if your repositories use *rulesets* rather than classic branch
protection, adding the App to a ruleset's bypass list is not enough. GitHub's
auto-merge does not honour ruleset bypasses, so the pull request would sit
blocked. Use the classic rule's push allowlist for this.

Being on the allowlist still does not let the App merge a pull request whose
checks are red; the required checks decide that.

## Undo

- **Stop it syncing:** delete the `TEMPLATE_SYNC_APP_PRIVATE_KEY` secret. The
  workflow goes back to printing a notice and the drift check keeps working.
- **Rotate the key** (if the `.pem` was ever somewhere it shouldn't be): App
  settings → **Private keys** → **Delete** the old one, **Generate** a new one,
  paste it into the secret again. Takes two minutes and nothing else changes.
- **Remove the App entirely:** App settings → **Advanced** → **Delete GitHub
  App**. Every token it ever issued stops working at once.

## Syncing by hand (the fallback)

From a checkout of this repository, on `main`, with the
[GitHub CLI](https://cli.github.com) signed in:

```bash
short=$(git rev-parse --short main)
scripts/template-sync.sh templates/records   https://github.com/lentago/uvularia-records-template.git sync/$short
scripts/template-sync.sh templates/ask-rules https://github.com/lentago/uvularia-rules-template.git   sync/$short
scripts/template-sync.sh templates/site      https://github.com/lentago/uvularia-site-template.git    sync/$short
# then, for each repository that printed changed=true:
gh pr create -R lentago/<that-repo> --head sync/$short --title "Sync from lentago/uvularia@$short" --body "By-hand sync of the subtree at $short."
gh pr merge  -R lentago/<that-repo> --auto --squash --delete-branch sync/$short
```

The script builds the branch from the template repository's own `main` and
copies the subtree over it, so the pull request is a plain diff. Check what it
did with `python3 scripts/template-drift.py --source-ref main`.
