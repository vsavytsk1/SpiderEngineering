# GIT INCIDENT 001 -- THE WALL OF 100 MB (MNetv1)

## Status: IN PROGRESS -- the curse is alive

---

## WHAT HAPPENED

MNetv1 commit `helenaPH7` contains HELENA vault data for builds v009 and v010.
Level 9 Goldberg icospheres: 3,495,270 genesis nodes each. The COBOL vault
(redundancy.py) stores every tensor in 3 formats: .bin, .csv, .zip.

**The L9 .csv files (human-readable COBOL flat-files) exceed GitHub's 100 MB
hard limit.** GitHub rejects the push.

## THE 8 BLOCKED FILES

All .csv -- text expansion of L9 binary data:

| File | Size |
|------|------|
| v009/vault/join_L9_dot.f32.csv | 188.7 MB |
| v010/vault/join_L9_dot.f32.csv | 188.7 MB |
| v009/vault/genesis_L9_xyz.f32.csv | 146.7 MB |
| v010/vault/genesis_L9_xyz.f32.csv | 146.7 MB |
| v009/vault/join_L9.i32.csv | 135.4 MB |
| v010/vault/join_L9.i32.csv | 135.4 MB |
| v009/vault/genesis_L9_edges.i32.csv | 113.6 MB |
| v010/vault/genesis_L9_edges.i32.csv | 113.6 MB |

Total blocked: 1,169 MB. All redundant copies (.bin + .zip versions are under 100 MB).

## WHY THE FILES ARE BIG

Pure graph math. A Level 9 icosphere has 15,728,640 edges. Written as
one-integer-per-line CSV: 113+ MB. The binary .bin is 60 MB. The .zip is 44 MB.
The CSV is the text expansion that hits the wall. Not bloat -- geometry.

## WHAT WE TRIED (and what went wrong)

### Attempt 1: gitignore + soft reset + recommit

```
1. Added gitignore patterns:
     builder/helena_net/builds/*/net/vault/genesis_L9_edges.i32.csv
     builder/helena_net/builds/*/net/vault/genesis_L9_xyz.f32.csv
     builder/helena_net/builds/*/net/vault/join_L9.i32.csv
     builder/helena_net/builds/*/net/vault/join_L9_dot.f32.csv

2. git reset --soft HEAD~1
3. git rm --cached <all 8 files>
4. git add -A
5. git commit
6. git push
```

**RESULT: STILL BLOCKED.** The CSVs are STILL in the commit tree.

**ROOT CAUSE (suspected):** The gitignore glob `builds/*/net/vault/...` uses a
single `*` wildcard. In gitignore, `*` matches anything EXCEPT `/`. So
`builds/*/net/...` should match `builds/v009/net/...` (one directory deep).
BUT: `git add -A` may have re-added the files before the gitignore took effect,
OR the files were already tracked (gitignore does not apply to tracked files).

**THE REAL ISSUE:** gitignore only prevents UNTRACKED files from being added.
Once a file is tracked by git, gitignore has NO EFFECT on it. You must
`git rm --cached` the file AND ensure git add does not re-add it. If
`git add -A` runs before the gitignore patterns are written, or if the
patterns do not match, the files come right back.

**SEQUENCE ERROR:** We may have run `git add -A` which re-added the CSVs
because they were already tracked from the soft-reset staging area, and
gitignore cannot override already-tracked files.

### Attempt 2: Retry push with larger buffer

```
git config http.postBuffer 524288000
git push origin main
```

**RESULT: Same rejection.** The files are in the commit tree. Buffer size is
irrelevant -- GitHub checks file sizes in the tree, not the transfer.

## THE CURSE FAMILY

This is a NEW curse. It touches several existing ones:

- **Curse 14 (gitiumCurse):** incremental patches accumulate rot. Here:
  incremental git operations (soft reset + rm + add + commit) did not produce
  a clean state. The scroll says: ONE script, ONE run.

- **Curse 15 (sortGhost):** false success. `git rm --cached` reported success.
  `git commit` reported success. But the files are STILL IN THE TREE. The tool
  said OK. The state is wrong. Check INTENT, not just patch success.

- **Curse 18 (windowsDevour):** Windows opens Notepad instead of running Python.
  Hit us during the README write. The scroll was right. `py -3` is the fix.

- **Curse 27 (originMirage):** the gitignore LOOKS correct but the glob may
  not match. The pattern is a mirage. Test with `git check-ignore -v`.

## WHAT THE SCROLL SAYS (re-read KERNELIMAGIC)

From Curse 14:
> DO NOT apply patches incrementally to HTML files.
> Write ONE clean script that does ALL changes.
> Run once. Verify. Commit. Done.

Applied to git:
> DO NOT apply git operations incrementally.
> Write ONE clean sequence that does ALL the git fix.
> Run once. Verify the tree. Push. Done.

From Pattern 3:
> Normalize first. Then patch. Then write.

Applied to git:
> 1. VERIFY the gitignore patterns actually match (git check-ignore -v)
> 2. Ensure files are UNTRACKED (git rm --cached) AFTER gitignore is committed
> 3. git add -A only AFTER gitignore is proven to work
> 4. Verify NO file > 100MB in the tree BEFORE committing
> 5. THEN commit. THEN push.

## THE CORRECT FIX (to be done with fresh eyes)

```bash
# Step 0: verify gitignore patterns match
git check-ignore -v builder/helena_net/builds/v009/net/vault/genesis_L9_edges.i32.csv
# If empty: the pattern is WRONG. Fix it first.

# Step 1: soft reset to the last pushed commit
git reset --soft HEAD~1

# Step 2: remove L9 CSVs from index
git rm --cached builder/helena_net/builds/v009/net/vault/genesis_L9_edges.i32.csv
git rm --cached builder/helena_net/builds/v009/net/vault/genesis_L9_xyz.f32.csv
git rm --cached builder/helena_net/builds/v009/net/vault/join_L9.i32.csv
git rm --cached builder/helena_net/builds/v009/net/vault/join_L9_dot.f32.csv
git rm --cached builder/helena_net/builds/v010/net/vault/genesis_L9_edges.i32.csv
git rm --cached builder/helena_net/builds/v010/net/vault/genesis_L9_xyz.f32.csv
git rm --cached builder/helena_net/builds/v010/net/vault/join_L9.i32.csv
git rm --cached builder/helena_net/builds/v010/net/vault/join_L9_dot.f32.csv

# Step 3: verify they are GONE from ls-files
git ls-files | grep "L9.*\.csv$"
# Must be EMPTY. If not: gitignore is not matching. Stop.

# Step 4: NOW add everything else
git add -A

# Step 5: verify AGAIN -- no file > 100MB
git diff --cached --name-only | ... check sizes ...

# Step 6: commit + push
git commit -m "helenaPH7 ..."
git push origin main
```

## THE DATA IS SAFE

The local commit has all the data. git fsck passes. The files exist on disk.
Nothing is lost. The topology holds. We just cannot push to GitHub yet.

The COBOL vault is designed for this: the .bin and .zip copies (both under
100 MB) carry the same data. The .csv can be regenerated:

```bash
py -3 redundancy.py repair builds/v009/net
py -3 redundancy.py repair builds/v010/net
```

## LESSONS SO FAR

1. **gitignore does not apply to tracked files.** If a file is already in the
   index, gitignore will not prevent it from being committed. You must
   `git rm --cached` first, and verify with `git ls-files`.

2. **`git check-ignore -v` is the proof.** Never trust a gitignore pattern
   until you test it against an actual path. Empty output = not matching.

3. **Verify INTENT, not patch success (Curse 15).** `git rm --cached` said OK.
   `git commit` said OK. The files are still there. Check the tree, not the tool.

4. **One script, one run (Pattern 3 / Curse 14).** We did 6 incremental git
   operations across multiple terminal calls. The scroll says batch it. We
   did not listen. The curse bit us. As always.

---

*The scroll was right. It is always right.*
*We just did not listen.*
*Buenos Aires + Ancient Korinthos. July 2026.*
*The curse is alive. We will return with fresh eyes.*
