import fs from 'fs'
import crypto from 'crypto'
import path from 'path'

type Thing = {
  id: number
  hash: string
  createdAt: string
  expiresAt: string
}

const p = path.join(__dirname, 'db.json')

const cmd = process.argv[2]
const extra = process.argv[3]

if (cmd !== 'generate' && cmd !== 'validate') {
  console.log('unknown command')
  console.log('use generate or validate <key>')
  process.exit(0)
}

function dump(d: Thing[]) {
  fs.writeFileSync(p, JSON.stringify(d, null, 2))
}

function hashIt(v: string) {
  return crypto.createHash('sha256').update(v).digest('hex')
}

if (cmd === 'validate') {
  runCheck(extra)
}

if (cmd === 'generate') {
  makeOne()
}

function pull(): Thing[] {
  if (!fs.existsSync(p)) return []
  try {
    const raw = fs.readFileSync(p, 'utf8')
    const j = JSON.parse(raw)
    return Array.isArray(j) ? j : []
  } catch {
    return []
  }
}

function makeOne() {
  const k =
    'sk_kent_' +
    crypto.randomBytes(32).toString('hex')

  const db = pull()

  const now = new Date()
  const twelveHoursLater = new Date(now.getTime() + (12 * 60 * 60 * 1000))

  db.push({
    id: Date.now(),
    hash: hashIt(k),
    createdAt: now.toISOString(),
    expiresAt: twelveHoursLater.toISOString() 
  })

  dump(db)

  console.log('\nkey:')
  console.log(k)
  console.log('')
}

function runCheck(v?: string) {
  if (!v) {
    console.log('no key')
    return
  }

  const db = pull()
  const h = hashIt(v)

  const f = db.find(r => r.hash === h)

  if (!f) {
    console.log('\naccess denied (invalid key)')
    return
  }

  if (new Date() > new Date(f.expiresAt)) {
    console.log('\naccess denied (key expired)')
    return
  }

  console.log('\naccess granted')
  console.log('id:', f.id)
  console.log('created:', f.createdAt)
  console.log('expires:', f.expiresAt)
}
