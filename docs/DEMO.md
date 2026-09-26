# Two-minute demo script

Record the screen at http://localhost:5173 with both servers already running. Speak slowly. Cut the pauses.

| Time | Do this | Say this |
| --- | --- | --- |
| 0:00 | Home page, no one signed in. Scroll the three published notes. | Anyone can read published notes. No account required. |
| 0:20 | Open "A boundary is a feature". Point at the like count and the comment box. | The full essay loads on this page. The feed itself does not send every body. |
| 0:35 | Sign in as `ravi@fieldnotes.local` / `Reader123!`. Like the post and add a comment. | A signed-in reader can respond. Ravi still cannot edit Mina's note. |
| 0:55 | Sign out. Sign in as `mina@fieldnotes.local` / `Author123!`. Open My desk. | Mina's desk is her tenant. The draft "Notes from the desk" is not on the public feed. |
| 1:15 | Open the draft, click Publish, then show it on the home page. | Publishing is the line between the private desk and the reading room. |
| 1:30 | Back on My desk, click Export CSV. | She can download only her own posts, as CSV, Excel, or PDF. |
| 1:45 | Sign out. Sign in as `admin@fieldnotes.local` / `Admin123!`. Open Admin. | Admin sees the role map, the audit trail, and the query plan for the feed index. |
| 2:00 | Stop on the audit table. | That is the week-one platform: public reading, private writing, and explicit permissions. |

## If a click fails

Refresh once. If the page cannot reach the API, check that `uvicorn` is still running on port 8000 and `npm run dev` is on port 5173.

## Hindi cue card

- Bina login ke home dikhao: published blogs sab padh sakte hain.
- Ravi se login karke like aur comment karo.
- Mina se login karke draft dikhao, publish karo, CSV export karo.
- Admin se audit log aur query plan dikhao.
