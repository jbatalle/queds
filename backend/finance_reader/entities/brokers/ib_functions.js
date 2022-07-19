
/**************** CROSS-BROWSER XML HTTP REQUEST AND XML PARSER ***************/

//var loader = new xhr.ContentLoader('GET','test.xml?id=123',true,handleGetResponse);

/* 
Wrapper function for constructing a request object
  Parameters:
	method: POST or GET
	url: local URL
	asynch: true or false
	respHandle: function name to handle response
	5th element: parameters for POST method
*/
var xhr = new Object();
xhr.READY_STATE_UNINITIALIZED = 0;
xhr.READY_STATE_LOADING = 1;
xhr.READY_STATE_LOADED = 2;
xhr.READY_STATE_INTERACTIVE = 3;
xhr.READY_STATE_COMPLETE = 4;


/* File: Templates/javascript/sha1.js */
/*
 * A JavaScript implementation of the Secure Hash Algorithm, SHA-1, as defined
 * in FIPS PUB 180-1
 * Copyright (C) Paul Johnston 2000.
 * See http://pajhome.org.uk/site/legal.html for details.
 */
/*
 * Modified by Tom Wu (tjw@cs.stanford.edu) for the
 * XYZ JavaScript implementation.
 */

/*
 * Convert a 32-bit number to a hex string with ms-byte first
 */
var hex_chr = "0123456789abcdef";
function hex(num)
{
  var str = "";
  for(var j = 7; j >= 0; j--)
    str += hex_chr.charAt((num >> (j * 4)) & 0x0F);
  return str;
}

/*
 * Convert a string to a sequence of 16-word blocks, stored as an array.
 * Append padding bits and the length, as described in the SHA1 standard.
 */
function str2blks_SHA1(str)
{
  var nblk = ((str.length + 8) >> 6) + 1;
  var blks = new Array(nblk * 16);
  for(var i = 0; i < nblk * 16; i++) blks[i] = 0;
  for(i = 0; i < str.length; i++)
    blks[i >> 2] |= str.charCodeAt(i) << (24 - (i % 4) * 8);
  blks[i >> 2] |= 0x80 << (24 - (i % 4) * 8);
  blks[nblk * 16 - 1] = str.length * 8;
  return blks;
}

/*
 * Input is in hex format - trailing odd nibble gets a zero appended.
 */
function hex2blks_SHA1(hex)
{
  var len = (hex.length + 1) >> 1;
  var nblk = ((len + 8) >> 6) + 1;
  var blks = new Array(nblk * 16);
  for(var i = 0; i < nblk * 16; i++) blks[i] = 0;
  for(i = 0; i < len; i++)
    blks[i >> 2] |= parseInt(hex.substr(2*i, 2), 16) << (24 - (i % 4) * 8);
  blks[i >> 2] |= 0x80 << (24 - (i % 4) * 8);
  blks[nblk * 16 - 1] = len * 8;
  return blks;
}

function ba2blks_SHA1(ba, off, len)
{
  var nblk = ((len + 8) >> 6) + 1;
  var blks = new Array(nblk * 16);
  for(var i = 0; i < nblk * 16; i++) blks[i] = 0;
  for(i = 0; i < len; i++)
    blks[i >> 2] |= (ba[off + i] & 0xFF) << (24 - (i % 4) * 8);
  blks[i >> 2] |= 0x80 << (24 - (i % 4) * 8);
  blks[nblk * 16 - 1] = len * 8;
  return blks;
}

/*
 * Add integers, wrapping at 2^32. This uses 16-bit operations internally 
 * to work around bugs in some JS interpreters.
 */
function add(x, y)
{
  var lsw = (x & 0xFFFF) + (y & 0xFFFF);
  var msw = (x >> 16) + (y >> 16) + (lsw >> 16);
  return (msw << 16) | (lsw & 0xFFFF);
}

/*
 * Bitwise rotate a 32-bit number to the left
 */
function rol(num, cnt)
{
  return (num << cnt) | (num >>> (32 - cnt));
}

/*
 * Perform the appropriate triplet combination function for the current
 * iteration
 */
function ft(t, b, c, d)
{
  if(t < 20) return (b & c) | ((~b) & d);
  if(t < 40) return b ^ c ^ d;
  if(t < 60) return (b & c) | (b & d) | (c & d);
  return b ^ c ^ d;
}

/*
 * Determine the appropriate additive constant for the current iteration
 */
function kt(t)
{
  return (t < 20) ?  1518500249 : (t < 40) ?  1859775393 :
         (t < 60) ? -1894007588 : -899497514;
}

/*
 * Take a string and return the hex representation of its SHA-1.
 */
function calcSHA1(str)
{
  return calcSHA1Blks(str2blks_SHA1(str));
}

function calcSHA1Hex(str)
{
  return calcSHA1Blks(hex2blks_SHA1(str));
}

function calcSHA1BA(ba)
{
  return calcSHA1Blks(ba2blks_SHA1(ba, 0, ba.length));
}

function calcSHA1BAEx(ba, off, len)
{
  return calcSHA1Blks(ba2blks_SHA1(ba, off, len));
}

function calcSHA1Blks(x)
{
  var s = calcSHA1Raw(x);
  return hex(s[0]) + hex(s[1]) + hex(s[2]) + hex(s[3]) + hex(s[4]);
}

function calcSHA1Raw(x)
{
  var w = new Array(80);

  var a =  1732584193;
  var b = -271733879;
  var c = -1732584194;
  var d =  271733878;
  var e = -1009589776;

  for(var i = 0; i < x.length; i += 16)
  {
    var olda = a;
    var oldb = b;
    var oldc = c;
    var oldd = d;
    var olde = e;

    for(var j = 0; j < 80; j++)
    {
      var t;
      if(j < 16) w[j] = x[i + j];
      else w[j] = rol(w[j-3] ^ w[j-8] ^ w[j-14] ^ w[j-16], 1);
      t = add(add(rol(a, 5), ft(j, b, c, d)), add(add(e, w[j]), kt(j)));
      e = d;
      d = c;
      c = rol(b, 30);
      b = a;
      a = t;
    }

    a = add(a, olda);
    b = add(b, oldb);
    c = add(c, oldc);
    d = add(d, oldd);
    e = add(e, olde);
  }
  return new Array(a, b, c, d, e);
}

function core_sha1(x, len) {
  x[len >> 5] |= 0x80 << (24 - len % 32);
  x[((len + 64 >> 9) << 4) + 15] = len;
  return calcSHA1Raw(x);
}


/* File: Templates/javascript/jsbn.js */
// Copyright (c) 2005  Tom Wu
// All Rights Reserved.
// See "LICENSE" for details.

// Basic JavaScript BN library - subset useful for RSA encryption.

// Bits per digit
var dbits;

// JavaScript engine analysis
var canary = 0xdeadbeefcafe;
var j_lm = ((canary&0xffffff)==0xefcafe);

// (public) Constructor
function BigInteger(a,b,c) {
  if(a != null)
    if("number" == typeof a) this.fromNumber(a,b,c);
    else if(b == null && "string" != typeof a) this.fromString(a,256);
    else this.fromString(a,b);
}

// return new, unset BigInteger
function nbi() { return new BigInteger(null); }

// am: Compute w_j += (x*this_i), propagate carries,
// c is initial carry, returns final carry.
// c < 3*dvalue, x < 2*dvalue, this_i < dvalue
// We need to select the fastest one that works in this environment.

// am1: use a single mult and divide to get the high bits,
// max digit bits should be 26 because
// max internal value = 2*dvalue^2-2*dvalue (< 2^53)
function am1(i,x,w,j,c,n) {
  while(--n >= 0) {
    var v = x*this[i++]+w[j]+c;
    c = Math.floor(v/0x4000000);
    w[j++] = v&0x3ffffff;
  }
  return c;
}
// am2 avoids a big mult-and-extract completely.
// Max digit bits should be <= 30 because we do bitwise ops
// on values up to 2*hdvalue^2-hdvalue-1 (< 2^31)
function am2(i,x,w,j,c,n) {
  var xl = x&0x7fff, xh = x>>15;
  while(--n >= 0) {
    var l = this[i]&0x7fff;
    var h = this[i++]>>15;
    var m = xh*l+h*xl;
    l = xl*l+((m&0x7fff)<<15)+w[j]+(c&0x3fffffff);
    c = (l>>>30)+(m>>>15)+xh*h+(c>>>30);
    w[j++] = l&0x3fffffff;
  }
  return c;
}
// Alternately, set max digit bits to 28 since some
// browsers slow down when dealing with 32-bit numbers.
function am3(i,x,w,j,c,n) {
  var xl = x&0x3fff, xh = x>>14;
  while(--n >= 0) {
    var l = this[i]&0x3fff;
    var h = this[i++]>>14;
    var m = xh*l+h*xl;
    l = xl*l+((m&0x3fff)<<14)+w[j]+c;
    c = (l>>28)+(m>>14)+xh*h;
    w[j++] = l&0xfffffff;
  }
  return c;
} // Mozilla/Netscape seems to prefer am3
  BigInteger.prototype.am = am3;
  dbits = 28;

BigInteger.prototype.DB = dbits;
BigInteger.prototype.DM = ((1<<dbits)-1);
BigInteger.prototype.DV = (1<<dbits);

var BI_FP = 52;
BigInteger.prototype.FV = Math.pow(2,BI_FP);
BigInteger.prototype.F1 = BI_FP-dbits;
BigInteger.prototype.F2 = 2*dbits-BI_FP;

// Digit conversions
var BI_RM = "0123456789abcdefghijklmnopqrstuvwxyz";
var BI_RC = new Array();
var rr,vv;
rr = "0".charCodeAt(0);
for(vv = 0; vv <= 9; ++vv) BI_RC[rr++] = vv;
rr = "a".charCodeAt(0);
for(vv = 10; vv < 36; ++vv) BI_RC[rr++] = vv;
rr = "A".charCodeAt(0);
for(vv = 10; vv < 36; ++vv) BI_RC[rr++] = vv;

function int2char(n) { return BI_RM.charAt(n); }
function intAt(s,i) {
  var c = BI_RC[s.charCodeAt(i)];
  return (c==null)?-1:c;
}

// (protected) copy this to r
function bnpCopyTo(r) {
  for(var i = this.t-1; i >= 0; --i) r[i] = this[i];
  r.t = this.t;
  r.s = this.s;
}

// (protected) set from integer value x, -DV <= x < DV
function bnpFromInt(x) {
  this.t = 1;
  this.s = (x<0)?-1:0;
  if(x > 0) this[0] = x;
  else if(x < -1) this[0] = x+DV;
  else this.t = 0;
}

// return bigint initialized to value
function nbv(i) { var r = nbi(); r.fromInt(i); return r; }

// (protected) set from string and radix
function bnpFromString(s,b) {
  var k;
  if(b == 16) k = 4;
  else if(b == 8) k = 3;
  else if(b == 256) k = 8; // byte array
  else if(b == 2) k = 1;
  else if(b == 32) k = 5;
  else if(b == 4) k = 2;
  else { this.fromRadix(s,b); return; }
  this.t = 0;
  this.s = 0;
  var i = s.length, mi = false, sh = 0;
  while(--i >= 0) {
    var x = (k==8)?s[i]&0xff:intAt(s,i);
    if(x < 0) {
      if(s.charAt(i) == "-") mi = true;
      continue;
    }
    mi = false;
    if(sh == 0)
      this[this.t++] = x;
    else if(sh+k > this.DB) {
      this[this.t-1] |= (x&((1<<(this.DB-sh))-1))<<sh;
      this[this.t++] = (x>>(this.DB-sh));
    }
    else  
      this[this.t-1] |= x<<sh;
    sh += k;
    if(sh >= this.DB) sh -= this.DB;
  }
  if(k == 8 && (s[0]&0x80) != 0) {
    this.s = -1;
    if(sh > 0) this[this.t-1] |= ((1<<(this.DB-sh))-1)<<sh;
  }
  this.clamp();
  if(mi) BigInteger.ZERO.subTo(this,this);
}

// (protected) clamp off excess high words
function bnpClamp() {
  var c = this.s&this.DM;
  while(this.t > 0 && this[this.t-1] == c) --this.t;
}

// (public) return string representation in given radix
function bnToString(b) {
  if(this.s < 0) return "-"+this.negate().toString(b);
  var k;
  if(b == 16) k = 4;
  else if(b == 8) k = 3;
  else if(b == 2) k = 1;
  else if(b == 32) k = 5;
  else if(b == 4) k = 2;
  else return this.toRadix(b);
  var km = (1<<k)-1, d, m = false, r = "", i = this.t;
  var p = this.DB-(i*this.DB)%k;
  if(i-- > 0) {
    if(p < this.DB && (d = this[i]>>p) > 0) { m = true; r = int2char(d); }
    while(i >= 0) {
      if(p < k) {
        d = (this[i]&((1<<p)-1))<<(k-p);
        d |= this[--i]>>(p+=this.DB-k);
      }
      else {
        d = (this[i]>>(p-=k))&km;
        if(p <= 0) { p += this.DB; --i; }
      }
      if(d > 0) m = true;
      if(m) r += int2char(d);
    }
  }
  return m?r:"0";
}

// (public) -this
function bnNegate() { var r = nbi(); BigInteger.ZERO.subTo(this,r); return r; }

// (public) |this|
function bnAbs() { return (this.s<0)?this.negate():this; }

// (public) return + if this > a, - if this < a, 0 if equal
function bnCompareTo(a) {
  console.log(this.s)
  console.log(a);
  var r = this.s-a.s;
  if(r != 0) return r;
  var i = this.t;
  r = i-a.t;
  if(r != 0) return r;
  while(--i >= 0) if((r=this[i]-a[i]) != 0) return r;
  return 0;
}

// returns bit length of the integer x
function nbits(x) {
  var r = 1, t;
  if((t=x>>>16) != 0) { x = t; r += 16; }
  if((t=x>>8) != 0) { x = t; r += 8; }
  if((t=x>>4) != 0) { x = t; r += 4; }
  if((t=x>>2) != 0) { x = t; r += 2; }
  if((t=x>>1) != 0) { x = t; r += 1; }
  return r;
}

// (public) return the number of bits in "this"
function bnBitLength() {
  if(this.t <= 0) return 0;
  return this.DB*(this.t-1)+nbits(this[this.t-1]^(this.s&this.DM));
}

// (protected) r = this << n*DB
function bnpDLShiftTo(n,r) {
  var i;
  for(i = this.t-1; i >= 0; --i) r[i+n] = this[i];
  for(i = n-1; i >= 0; --i) r[i] = 0;
  r.t = this.t+n;
  r.s = this.s;
}

// (protected) r = this >> n*DB
function bnpDRShiftTo(n,r) {
  for(var i = n; i < this.t; ++i) r[i-n] = this[i];
  r.t = Math.max(this.t-n,0);
  r.s = this.s;
}

// (protected) r = this << n
function bnpLShiftTo(n,r) {
  var bs = n%this.DB;
  var cbs = this.DB-bs;
  var bm = (1<<cbs)-1;
  var ds = Math.floor(n/this.DB), c = (this.s<<bs)&this.DM, i;
  for(i = this.t-1; i >= 0; --i) {
    r[i+ds+1] = (this[i]>>cbs)|c;
    c = (this[i]&bm)<<bs;
  }
  for(i = ds-1; i >= 0; --i) r[i] = 0;
  r[ds] = c;
  r.t = this.t+ds+1;
  r.s = this.s;
  r.clamp();
}

// (protected) r = this >> n
function bnpRShiftTo(n,r) {
  r.s = this.s;
  var ds = Math.floor(n/this.DB);
  if(ds >= this.t) { r.t = 0; return; }
  var bs = n%this.DB;
  var cbs = this.DB-bs;
  var bm = (1<<bs)-1;
  r[0] = this[ds]>>bs;
  for(var i = ds+1; i < this.t; ++i) {
    r[i-ds-1] |= (this[i]&bm)<<cbs;
    r[i-ds] = this[i]>>bs;
  }
  if(bs > 0) r[this.t-ds-1] |= (this.s&bm)<<cbs;
  r.t = this.t-ds;
  r.clamp();
}

// (protected) r = this - a
function bnpSubTo(a,r) {
  var i = 0, c = 0, m = Math.min(a.t,this.t);
  while(i < m) {
    c += this[i]-a[i];
    r[i++] = c&this.DM;
    c >>= this.DB;
  }
  if(a.t < this.t) {
    c -= a.s;
    while(i < this.t) {
      c += this[i];
      r[i++] = c&this.DM;
      c >>= this.DB;
    }
    c += this.s;
  }
  else {
    c += this.s;
    while(i < a.t) {
      c -= a[i];
      r[i++] = c&this.DM;
      c >>= this.DB;
    }
    c -= a.s;
  }
  r.s = (c<0)?-1:0;
  if(c < -1) r[i++] = this.DV+c;
  else if(c > 0) r[i++] = c;
  r.t = i;
  r.clamp();
}

// (protected) r = this * a, r != this,a (HAC 14.12)
// "this" should be the larger one if appropriate.
function bnpMultiplyTo(a,r) {
  var x = this.abs(), y = a.abs();
  var i = x.t;
  r.t = i+y.t;
  while(--i >= 0) r[i] = 0;
  for(i = 0; i < y.t; ++i) r[i+x.t] = x.am(0,y[i],r,i,0,x.t);
  r.s = 0;
  r.clamp();
  if(this.s != a.s) BigInteger.ZERO.subTo(r,r);
}

// (protected) r = this^2, r != this (HAC 14.16)
function bnpSquareTo(r) {
  var x = this.abs();
  var i = r.t = 2*x.t;
  while(--i >= 0) r[i] = 0;
  for(i = 0; i < x.t-1; ++i) {
    var c = x.am(i,x[i],r,2*i,0,1);
    if((r[i+x.t]+=x.am(i+1,2*x[i],r,2*i+1,c,x.t-i-1)) >= x.DV) {
      r[i+x.t] -= x.DV;
      r[i+x.t+1] = 1;
    }
  }
  if(r.t > 0) r[r.t-1] += x.am(i,x[i],r,2*i,0,1);
  r.s = 0;
  r.clamp();
}

// (protected) divide this by m, quotient and remainder to q, r (HAC 14.20)
// r != q, this != m.  q or r may be null.
function bnpDivRemTo(m,q,r) {
  var pm = m.abs();
  if(pm.t <= 0) return;
  var pt = this.abs();
  if(pt.t < pm.t) {
    if(q != null) q.fromInt(0);
    if(r != null) this.copyTo(r);
    return;
  }
  if(r == null) r = nbi();
  var y = nbi(), ts = this.s, ms = m.s;
  var nsh = this.DB-nbits(pm[pm.t-1]);	// normalize modulus
  if(nsh > 0) { pm.lShiftTo(nsh,y); pt.lShiftTo(nsh,r); }
  else { pm.copyTo(y); pt.copyTo(r); }
  var ys = y.t;
  var y0 = y[ys-1];
  if(y0 == 0) return;
  var yt = y0*(1<<this.F1)+((ys>1)?y[ys-2]>>this.F2:0);
  var d1 = this.FV/yt, d2 = (1<<this.F1)/yt, e = 1<<this.F2;
  var i = r.t, j = i-ys, t = (q==null)?nbi():q;
  y.dlShiftTo(j,t);
  if(r.compareTo(t) >= 0) {
    r[r.t++] = 1;
    r.subTo(t,r);
  }
  BigInteger.ONE.dlShiftTo(ys,t);
  t.subTo(y,y);	// "negative" y so we can replace sub with am later
  while(y.t < ys) y[y.t++] = 0;
  while(--j >= 0) {
    // Estimate quotient digit
    var qd = (r[--i]==y0)?this.DM:Math.floor(r[i]*d1+(r[i-1]+e)*d2);
    if((r[i]+=y.am(0,qd,r,j,0,ys)) < qd) {	// Try it out
      y.dlShiftTo(j,t);
      r.subTo(t,r);
      while(r[i] < --qd) r.subTo(t,r);
    }
  }
  if(q != null) {
    r.drShiftTo(ys,q);
    if(ts != ms) BigInteger.ZERO.subTo(q,q);
  }
  r.t = ys;
  r.clamp();
  if(nsh > 0) r.rShiftTo(nsh,r);	// Denormalize remainder
  if(ts < 0) BigInteger.ZERO.subTo(r,r);
}

// (public) this mod a
function bnMod(a) {
  var r = nbi();
  this.abs().divRemTo(a,null,r);
  if(this.s < 0 && r.compareTo(BigInteger.ZERO) > 0) a.subTo(r,r);
  return r;
}

// Modular reduction using "classic" algorithm
function Classic(m) { this.m = m; }
function cConvert(x) {
  if(x.s < 0 || x.compareTo(this.m) >= 0) return x.mod(this.m);
  else return x;
}
function cRevert(x) { return x; }
function cReduce(x) { x.divRemTo(this.m,null,x); }
function cMulTo(x,y,r) { x.multiplyTo(y,r); this.reduce(r); }
function cSqrTo(x,r) { x.squareTo(r); this.reduce(r); }

Classic.prototype.convert = cConvert;
Classic.prototype.revert = cRevert;
Classic.prototype.reduce = cReduce;
Classic.prototype.mulTo = cMulTo;
Classic.prototype.sqrTo = cSqrTo;

// (protected) return "-1/this % 2^DB"; useful for Mont. reduction
// justification:
//         xy == 1 (mod m)
//         xy =  1+km
//   xy(2-xy) = (1+km)(1-km)
// x[y(2-xy)] = 1-k^2m^2
// x[y(2-xy)] == 1 (mod m^2)
// if y is 1/x mod m, then y(2-xy) is 1/x mod m^2
// should reduce x and y(2-xy) by m^2 at each step to keep size bounded.
// JS multiply "overflows" differently from C/C++, so care is needed here.
function bnpInvDigit() {
  if(this.t < 1) return 0;
  var x = this[0];
  if((x&1) == 0) return 0;
  var y = x&3;		// y == 1/x mod 2^2
  y = (y*(2-(x&0xf)*y))&0xf;	// y == 1/x mod 2^4
  y = (y*(2-(x&0xff)*y))&0xff;	// y == 1/x mod 2^8
  y = (y*(2-(((x&0xffff)*y)&0xffff)))&0xffff;	// y == 1/x mod 2^16
  // last step - calculate inverse mod DV directly;
  // assumes 16 < DB <= 32 and assumes ability to handle 48-bit ints
  y = (y*(2-x*y%this.DV))%this.DV;		// y == 1/x mod 2^dbits
  // we really want the negative inverse, and -DV < y < DV
  return (y>0)?this.DV-y:-y;
}

// Montgomery reduction
function Montgomery(m) {
  this.m = m;
  this.mp = m.invDigit();
  this.mpl = this.mp&0x7fff;
  this.mph = this.mp>>15;
  this.um = (1<<(m.DB-15))-1;
  this.mt2 = 2*m.t;
}

// xR mod m
function montConvert(x) {
  var r = nbi();
  x.abs().dlShiftTo(this.m.t,r);
  r.divRemTo(this.m,null,r);
  if(x.s < 0 && r.compareTo(BigInteger.ZERO) > 0) this.m.subTo(r,r);
  return r;
}

// x/R mod m
function montRevert(x) {
  var r = nbi();
  x.copyTo(r);
  this.reduce(r);
  return r;
}

// x = x/R mod m (HAC 14.32)
function montReduce(x) {
  while(x.t <= this.mt2)	// pad x so am has enough room later
    x[x.t++] = 0;
  for(var i = 0; i < this.m.t; ++i) {
    // faster way of calculating u0 = x[i]*mp mod DV
    var j = x[i]&0x7fff;
    var u0 = (j*this.mpl+(((j*this.mph+(x[i]>>15)*this.mpl)&this.um)<<15))&x.DM;
    // use am to combine the multiply-shift-add into one call
    j = i+this.m.t;
    x[j] += this.m.am(0,u0,x,i,0,this.m.t);
    // propagate carry
    while(x[j] >= x.DV) { x[j] -= x.DV; x[++j]++; }
  }
  x.clamp();
  x.drShiftTo(this.m.t,x);
  if(x.compareTo(this.m) >= 0) x.subTo(this.m,x);
}

// r = "x^2/R mod m"; x != r
function montSqrTo(x,r) { x.squareTo(r); this.reduce(r); }

// r = "xy/R mod m"; x,y != r
function montMulTo(x,y,r) { x.multiplyTo(y,r); this.reduce(r); }

Montgomery.prototype.convert = montConvert;
Montgomery.prototype.revert = montRevert;
Montgomery.prototype.reduce = montReduce;
Montgomery.prototype.mulTo = montMulTo;
Montgomery.prototype.sqrTo = montSqrTo;

// (protected) true iff this is even
function bnpIsEven() { return ((this.t>0)?(this[0]&1):this.s) == 0; }

// (protected) this^e, e < 2^32, doing sqr and mul with "r" (HAC 14.79)
function bnpExp(e,z) {
  if(e > 0xffffffff || e < 1) return BigInteger.ONE;
  var r = nbi(), r2 = nbi(), g = z.convert(this), i = nbits(e)-1;
  g.copyTo(r);
  while(--i >= 0) {
    z.sqrTo(r,r2);
    if((e&(1<<i)) > 0) z.mulTo(r2,g,r);
    else { var t = r; r = r2; r2 = t; }
  }
  return z.revert(r);
}

// (public) this^e % m, 0 <= e < 2^32
function bnModPowInt(e,m) {
  var z;
  if(e < 256 || m.isEven()) z = new Classic(m); else z = new Montgomery(m);
  return this.exp(e,z);
}

// protected
BigInteger.prototype.copyTo = bnpCopyTo;
BigInteger.prototype.fromInt = bnpFromInt;
BigInteger.prototype.fromString = bnpFromString;
BigInteger.prototype.clamp = bnpClamp;
BigInteger.prototype.dlShiftTo = bnpDLShiftTo;
BigInteger.prototype.drShiftTo = bnpDRShiftTo;
BigInteger.prototype.lShiftTo = bnpLShiftTo;
BigInteger.prototype.rShiftTo = bnpRShiftTo;
BigInteger.prototype.subTo = bnpSubTo;
BigInteger.prototype.multiplyTo = bnpMultiplyTo;
BigInteger.prototype.squareTo = bnpSquareTo;
BigInteger.prototype.divRemTo = bnpDivRemTo;
BigInteger.prototype.invDigit = bnpInvDigit;
BigInteger.prototype.isEven = bnpIsEven;
BigInteger.prototype.exp = bnpExp;

// public
BigInteger.prototype.toString = bnToString;
BigInteger.prototype.negate = bnNegate;
BigInteger.prototype.abs = bnAbs;
BigInteger.prototype.compareTo = bnCompareTo;
BigInteger.prototype.bitLength = bnBitLength;
BigInteger.prototype.mod = bnMod;
BigInteger.prototype.modPowInt = bnModPowInt;

// "constants"
BigInteger.ZERO = nbv(0);
BigInteger.ONE = nbv(1);


/* File: Templates/javascript/jsbn2.js */
// Copyright (c) 2005  Tom Wu
// All Rights Reserved.
// See "LICENSE" for details.

// Extended JavaScript BN functions, required for RSA private ops.

// (public)
function bnClone() { var r = nbi(); this.copyTo(r); return r; }

// (public) return value as integer
function bnIntValue() {
  if(this.s < 0) {
    if(this.t == 1) return this[0]-this.DV;
    else if(this.t == 0) return -1;
  }
  else if(this.t == 1) return this[0];
  else if(this.t == 0) return 0;
  // assumes 16 < DB < 32
  return ((this[1]&((1<<(32-this.DB))-1))<<this.DB)|this[0];
}

// (public) return value as byte
function bnByteValue() { return (this.t==0)?this.s:(this[0]<<24)>>24; }

// (public) return value as short (assumes DB>=16)
function bnShortValue() { return (this.t==0)?this.s:(this[0]<<16)>>16; }

// (protected) return x s.t. r^x < DV
function bnpChunkSize(r) { return Math.floor(Math.LN2*this.DB/Math.log(r)); }

// (public) 0 if this == 0, 1 if this > 0
function bnSigNum() {
  if(this.s < 0) return -1;
  else if(this.t <= 0 || (this.t == 1 && this[0] <= 0)) return 0;
  else return 1;
}

// (protected) convert to radix string
function bnpToRadix(b) {
  if(b == null) b = 10;
  if(this.signum() == 0 || b < 2 || b > 36) return "0";
  var cs = this.chunkSize(b);
  var a = Math.pow(b,cs);
  var d = nbv(a), y = nbi(), z = nbi(), r = "";
  this.divRemTo(d,y,z);
  while(y.signum() > 0) {
    r = (a+z.intValue()).toString(b).substr(1) + r;
    y.divRemTo(d,y,z);
  }
  return z.intValue().toString(b) + r;
}

// (protected) convert from radix string
function bnpFromRadix(s,b) {
  this.fromInt(0);
  if(b == null) b = 10;
  var cs = this.chunkSize(b);
  var d = Math.pow(b,cs), mi = false, j = 0, w = 0;
  for(var i = 0; i < s.length; ++i) {
    var x = intAt(s,i);
    if(x < 0) {
      if(s.charAt(i) == "-" && this.signum() == 0) mi = true;
      continue;
    }
    w = b*w+x;
    if(++j >= cs) {
      this.dMultiply(d);
      this.dAddOffset(w,0);
      j = 0;
      w = 0;
    }
  }
  if(j > 0) {
    this.dMultiply(Math.pow(b,j));
    this.dAddOffset(w,0);
  }
  if(mi) BigInteger.ZERO.subTo(this,this);
}

// (protected) alternate constructor
function bnpFromNumber(a,b,c) {
  if("number" == typeof b) {
    // new BigInteger(int,int,RNG)
    if(a < 2) this.fromInt(1);
    else {
      this.fromNumber(a,c);
      if(!this.testBit(a-1))	// force MSB set
        this.bitwiseTo(BigInteger.ONE.shiftLeft(a-1),op_or,this);
      if(this.isEven()) this.dAddOffset(1,0); // force odd
      while(!this.isProbablePrime(b)) {
        this.dAddOffset(2,0);
        if(this.bitLength() > a) this.subTo(BigInteger.ONE.shiftLeft(a-1),this);
      }
    }
  }
  else {
    // new BigInteger(int,RNG)
    var x = new Array(), t = a&7;
    x.length = (a>>3)+1;
    b.nextBytes(x);
    if(t > 0) x[0] &= ((1<<t)-1); else x[0] = 0;
    this.fromString(x,256);
  }
}

// (public) convert to bigendian byte array
function bnToByteArray() {
  var i = this.t, r = new Array();
  r[0] = this.s;
  var p = this.DB-(i*this.DB)%8, d, k = 0;
  if(i-- > 0) {
    if(p < this.DB && (d = this[i]>>p) != (this.s&this.DM)>>p)
      r[k++] = d|(this.s<<(this.DB-p));
    while(i >= 0) {
      if(p < 8) {
        d = (this[i]&((1<<p)-1))<<(8-p);
        d |= this[--i]>>(p+=this.DB-8);
      }
      else {
        d = (this[i]>>(p-=8))&0xff;
        if(p <= 0) { p += this.DB; --i; }
      }
      if((d&0x80) != 0) d |= -256;
      if(k == 0 && (this.s&0x80) != (d&0x80)) ++k;
      if(k > 0 || d != this.s) r[k++] = d;
    }
  }
  return r;
}

function bnEquals(a) { return(this.compareTo(a)==0); }
function bnMin(a) { return(this.compareTo(a)<0)?this:a; }
function bnMax(a) { return(this.compareTo(a)>0)?this:a; }

// (protected) r = this op a (bitwise)
function bnpBitwiseTo(a,op,r) {
  var i, f, m = Math.min(a.t,this.t);
  for(i = 0; i < m; ++i) r[i] = op(this[i],a[i]);
  if(a.t < this.t) {
    f = a.s&this.DM;
    for(i = m; i < this.t; ++i) r[i] = op(this[i],f);
    r.t = this.t;
  }
  else {
    f = this.s&this.DM;
    for(i = m; i < a.t; ++i) r[i] = op(f,a[i]);
    r.t = a.t;
  }
  r.s = op(this.s,a.s);
  r.clamp();
}

// (public) this & a
function op_and(x,y) { return x&y; }
function bnAnd(a) { var r = nbi(); this.bitwiseTo(a,op_and,r); return r; }

// (public) this | a
function op_or(x,y) { return x|y; }
function bnOr(a) { var r = nbi(); this.bitwiseTo(a,op_or,r); return r; }

// (public) this ^ a
function op_xor(x,y) { return x^y; }
function bnXor(a) { var r = nbi(); this.bitwiseTo(a,op_xor,r); return r; }

// (public) this & ~a
function op_andnot(x,y) { return x&~y; }
function bnAndNot(a) { var r = nbi(); this.bitwiseTo(a,op_andnot,r); return r; }

// (public) ~this
function bnNot() {
  var r = nbi();
  for(var i = 0; i < this.t; ++i) r[i] = this.DM&~this[i];
  r.t = this.t;
  r.s = ~this.s;
  return r;
}

// (public) this << n
function bnShiftLeft(n) {
  var r = nbi();
  if(n < 0) this.rShiftTo(-n,r); else this.lShiftTo(n,r);
  return r;
}

// (public) this >> n
function bnShiftRight(n) {
  var r = nbi();
  if(n < 0) this.lShiftTo(-n,r); else this.rShiftTo(n,r);
  return r;
}

// return index of lowest 1-bit in x, x < 2^31
function lbit(x) {
  if(x == 0) return -1;
  var r = 0;
  if((x&0xffff) == 0) { x >>= 16; r += 16; }
  if((x&0xff) == 0) { x >>= 8; r += 8; }
  if((x&0xf) == 0) { x >>= 4; r += 4; }
  if((x&3) == 0) { x >>= 2; r += 2; }
  if((x&1) == 0) ++r;
  return r;
}

// (public) returns index of lowest 1-bit (or -1 if none)
function bnGetLowestSetBit() {
  for(var i = 0; i < this.t; ++i)
    if(this[i] != 0) return i*this.DB+lbit(this[i]);
  if(this.s < 0) return this.t*this.DB;
  return -1;
}

// return number of 1 bits in x
function cbit(x) {
  var r = 0;
  while(x != 0) { x &= x-1; ++r; }
  return r;
}

// (public) return number of set bits
function bnBitCount() {
  var r = 0, x = this.s&this.DM;
  for(var i = 0; i < this.t; ++i) r += cbit(this[i]^x);
  return r;
}

// (public) true iff nth bit is set
function bnTestBit(n) {
  var j = Math.floor(n/this.DB);
  if(j >= this.t) return(this.s!=0);
  return((this[j]&(1<<(n%this.DB)))!=0);
}

// (protected) this op (1<<n)
function bnpChangeBit(n,op) {
  var r = BigInteger.ONE.shiftLeft(n);
  this.bitwiseTo(r,op,r);
  return r;
}

// (public) this | (1<<n)
function bnSetBit(n) { return this.changeBit(n,op_or); }

// (public) this & ~(1<<n)
function bnClearBit(n) { return this.changeBit(n,op_andnot); }

// (public) this ^ (1<<n)
function bnFlipBit(n) { return this.changeBit(n,op_xor); }

// (protected) r = this + a
function bnpAddTo(a,r) {
  var i = 0, c = 0, m = Math.min(a.t,this.t);
  while(i < m) {
    c += this[i]+a[i];
    r[i++] = c&this.DM;
    c >>= this.DB;
  }
  if(a.t < this.t) {
    c += a.s;
    while(i < this.t) {
      c += this[i];
      r[i++] = c&this.DM;
      c >>= this.DB;
    }
    c += this.s;
  }
  else {
    c += this.s;
    while(i < a.t) {
      c += a[i];
      r[i++] = c&this.DM;
      c >>= this.DB;
    }
    c += a.s;
  }
  r.s = (c<0)?-1:0;
  if(c > 0) r[i++] = c;
  else if(c < -1) r[i++] = this.DV+c;
  r.t = i;
  r.clamp();
}

// (public) this + a
function bnAdd(a) { var r = nbi(); this.addTo(a,r); return r; }

// (public) this - a
function bnSubtract(a) { var r = nbi(); this.subTo(a,r); return r; }

// (public) this * a
function bnMultiply(a) { var r = nbi(); this.multiplyTo(a,r); return r; }

// (public) this / a
function bnDivide(a) { var r = nbi(); this.divRemTo(a,r,null); return r; }

// (public) this % a
function bnRemainder(a) { var r = nbi(); this.divRemTo(a,null,r); return r; }

// (public) [this/a,this%a]
function bnDivideAndRemainder(a) {
  var q = nbi(), r = nbi();
  this.divRemTo(a,q,r);
  return new Array(q,r);
}

// (protected) this *= n, this >= 0, 1 < n < DV
function bnpDMultiply(n) {
  this[this.t] = this.am(0,n-1,this,0,0,this.t);
  ++this.t;
  this.clamp();
}

// (protected) this += n << w words, this >= 0
function bnpDAddOffset(n,w) {
  while(this.t <= w) this[this.t++] = 0;
  this[w] += n;
  while(this[w] >= this.DV) {
    this[w] -= this.DV;
    if(++w >= this.t) this[this.t++] = 0;
    ++this[w];
  }
}

// A "null" reducer
function NullExp() {}
function nNop(x) { return x; }
function nMulTo(x,y,r) { x.multiplyTo(y,r); }
function nSqrTo(x,r) { x.squareTo(r); }

NullExp.prototype.convert = nNop;
NullExp.prototype.revert = nNop;
NullExp.prototype.mulTo = nMulTo;
NullExp.prototype.sqrTo = nSqrTo;

// (public) this^e
function bnPow(e) { return this.exp(e,new NullExp()); }

// (protected) r = lower n words of "this * a", a.t <= n
// "this" should be the larger one if appropriate.
function bnpMultiplyLowerTo(a,n,r) {
  var i = Math.min(this.t+a.t,n);
  r.s = 0; // assumes a,this >= 0
  r.t = i;
  while(i > 0) r[--i] = 0;
  var j;
  for(j = r.t-this.t; i < j; ++i) r[i+this.t] = this.am(0,a[i],r,i,0,this.t);
  for(j = Math.min(a.t,n); i < j; ++i) this.am(0,a[i],r,i,0,n-i);
  r.clamp();
}

// (protected) r = "this * a" without lower n words, n > 0
// "this" should be the larger one if appropriate.
function bnpMultiplyUpperTo(a,n,r) {
  --n;
  var i = r.t = this.t+a.t-n;
  r.s = 0; // assumes a,this >= 0
  while(--i >= 0) r[i] = 0;
  for(i = Math.max(n-this.t,0); i < a.t; ++i)
    r[this.t+i-n] = this.am(n-i,a[i],r,0,0,this.t+i-n);
  r.clamp();
  r.drShiftTo(1,r);
}

// Barrett modular reduction
function Barrett(m) {
  // setup Barrett
  this.r2 = nbi();
  this.q3 = nbi();
  BigInteger.ONE.dlShiftTo(2*m.t,this.r2);
  this.mu = this.r2.divide(m);
  this.m = m;
}

function barrettConvert(x) {
  if(x.s < 0 || x.t > 2*this.m.t) return x.mod(this.m);
  else if(x.compareTo(this.m) < 0) return x;
  else { var r = nbi(); x.copyTo(r); this.reduce(r); return r; }
}

function barrettRevert(x) { return x; }

// x = x mod m (HAC 14.42)
function barrettReduce(x) {
  x.drShiftTo(this.m.t-1,this.r2);
  if(x.t > this.m.t+1) { x.t = this.m.t+1; x.clamp(); }
  this.mu.multiplyUpperTo(this.r2,this.m.t+1,this.q3);
  this.m.multiplyLowerTo(this.q3,this.m.t+1,this.r2);
  while(x.compareTo(this.r2) < 0) x.dAddOffset(1,this.m.t+1);
  x.subTo(this.r2,x);
  while(x.compareTo(this.m) >= 0) x.subTo(this.m,x);
}

// r = x^2 mod m; x != r
function barrettSqrTo(x,r) { x.squareTo(r); this.reduce(r); }

// r = x*y mod m; x,y != r
function barrettMulTo(x,y,r) { x.multiplyTo(y,r); this.reduce(r); }

Barrett.prototype.convert = barrettConvert;
Barrett.prototype.revert = barrettRevert;
Barrett.prototype.reduce = barrettReduce;
Barrett.prototype.mulTo = barrettMulTo;
Barrett.prototype.sqrTo = barrettSqrTo;

// (public) this^e % m (HAC 14.85)
function bnModPow(e,m) {
  var i = e.bitLength(), k, r = nbv(1), z;
  if(i <= 0) return r;
  else if(i < 18) k = 1;
  else if(i < 48) k = 3;
  else if(i < 144) k = 4;
  else if(i < 768) k = 5;
  else k = 6;
  if(i < 8)
    z = new Classic(m);
  else if(m.isEven())
    z = new Barrett(m);
  else
    z = new Montgomery(m);

  // precomputation
  var g = new Array(), n = 3, k1 = k-1, km = (1<<k)-1;
  g[1] = z.convert(this);
  if(k > 1) {
    var g2 = nbi();
    z.sqrTo(g[1],g2);
    while(n <= km) {
      g[n] = nbi();
      z.mulTo(g2,g[n-2],g[n]);
      n += 2;
    }
  }

  var j = e.t-1, w, is1 = true, r2 = nbi(), t;
  i = nbits(e[j])-1;
  while(j >= 0) {
    if(i >= k1) w = (e[j]>>(i-k1))&km;
    else {
      w = (e[j]&((1<<(i+1))-1))<<(k1-i);
      if(j > 0) w |= e[j-1]>>(this.DB+i-k1);
    }

    n = k;
    while((w&1) == 0) { w >>= 1; --n; }
    if((i -= n) < 0) { i += this.DB; --j; }
    if(is1) {	// ret == 1, don't bother squaring or multiplying it
      g[w].copyTo(r);
      is1 = false;
    }
    else {
      while(n > 1) { z.sqrTo(r,r2); z.sqrTo(r2,r); n -= 2; }
      if(n > 0) z.sqrTo(r,r2); else { t = r; r = r2; r2 = t; }
      z.mulTo(r2,g[w],r);
    }

    while(j >= 0 && (e[j]&(1<<i)) == 0) {
      z.sqrTo(r,r2); t = r; r = r2; r2 = t;
      if(--i < 0) { i = this.DB-1; --j; }
    }
  }
  return z.revert(r);
}

// (public) gcd(this,a) (HAC 14.54)
function bnGCD(a) {
  var x = (this.s<0)?this.negate():this.clone();
  var y = (a.s<0)?a.negate():a.clone();
  if(x.compareTo(y) < 0) { var t = x; x = y; y = t; }
  var i = x.getLowestSetBit(), g = y.getLowestSetBit();
  if(g < 0) return x;
  if(i < g) g = i;
  if(g > 0) {
    x.rShiftTo(g,x);
    y.rShiftTo(g,y);
  }
  while(x.signum() > 0) {
    if((i = x.getLowestSetBit()) > 0) x.rShiftTo(i,x);
    if((i = y.getLowestSetBit()) > 0) y.rShiftTo(i,y);
    if(x.compareTo(y) >= 0) {
      x.subTo(y,x);
      x.rShiftTo(1,x);
    }
    else {
      y.subTo(x,y);
      y.rShiftTo(1,y);
    }
  }
  if(g > 0) y.lShiftTo(g,y);
  return y;
}

// (protected) this % n, n < 2^26
function bnpModInt(n) {
  if(n <= 0) return 0;
  var d = this.DV%n, r = (this.s<0)?n-1:0;
  if(this.t > 0)
    if(d == 0) r = this[0]%n;
    else for(var i = this.t-1; i >= 0; --i) r = (d*r+this[i])%n;
  return r;
}

// (public) 1/this % m (HAC 14.61)
function bnModInverse(m) {
  var ac = m.isEven();
  if((this.isEven() && ac) || m.signum() == 0) return BigInteger.ZERO;
  var u = m.clone(), v = this.clone();
  var a = nbv(1), b = nbv(0), c = nbv(0), d = nbv(1);
  while(u.signum() != 0) {
    while(u.isEven()) {
      u.rShiftTo(1,u);
      if(ac) {
        if(!a.isEven() || !b.isEven()) { a.addTo(this,a); b.subTo(m,b); }
        a.rShiftTo(1,a);
      }
      else if(!b.isEven()) b.subTo(m,b);
      b.rShiftTo(1,b);
    }
    while(v.isEven()) {
      v.rShiftTo(1,v);
      if(ac) {
        if(!c.isEven() || !d.isEven()) { c.addTo(this,c); d.subTo(m,d); }
        c.rShiftTo(1,c);
      }
      else if(!d.isEven()) d.subTo(m,d);
      d.rShiftTo(1,d);
    }
    if(u.compareTo(v) >= 0) {
      u.subTo(v,u);
      if(ac) a.subTo(c,a);
      b.subTo(d,b);
    }
    else {
      v.subTo(u,v);
      if(ac) c.subTo(a,c);
      d.subTo(b,d);
    }
  }
  if(v.compareTo(BigInteger.ONE) != 0) return BigInteger.ZERO;
  if(d.compareTo(m) >= 0) return d.subtract(m);
  if(d.signum() < 0) d.addTo(m,d); else return d;
  if(d.signum() < 0) return d.add(m); else return d;
}

var lowprimes = [2,3,5,7,11,13,17,19,23,29,31,37,41,43,47,53,59,61,67,71,73,79,83,89,97,101,103,107,109,113,127,131,137,139,149,151,157,163,167,173,179,181,191,193,197,199,211,223,227,229,233,239,241,251,257,263,269,271,277,281,283,293,307,311,313,317,331,337,347,349,353,359,367,373,379,383,389,397,401,409,419,421,431,433,439,443,449,457,461,463,467,479,487,491,499,503,509];
var lplim = (1<<26)/lowprimes[lowprimes.length-1];

// (public) test primality with certainty >= 1-.5^t
function bnIsProbablePrime(t) {
  var i, x = this.abs();
  if(x.t == 1 && x[0] <= lowprimes[lowprimes.length-1]) {
    for(i = 0; i < lowprimes.length; ++i)
      if(x[0] == lowprimes[i]) return true;
    return false;
  }
  if(x.isEven()) return false;
  i = 1;
  while(i < lowprimes.length) {
    var m = lowprimes[i], j = i+1;
    while(j < lowprimes.length && m < lplim) m *= lowprimes[j++];
    m = x.modInt(m);
    while(i < j) if(m%lowprimes[i++] == 0) return false;
  }
  return x.millerRabin(t);
}

// (protected) true if probably prime (HAC 4.24, Miller-Rabin)
function bnpMillerRabin(t) {
  var n1 = this.subtract(BigInteger.ONE);
  var k = n1.getLowestSetBit();
  if(k <= 0) return false;
  var r = n1.shiftRight(k);
  t = (t+1)>>1;
  if(t > lowprimes.length) t = lowprimes.length;
  var a = nbi();
  for(var i = 0; i < t; ++i) {
    a.fromInt(lowprimes[i]);
    var y = a.modPow(r,this);
    if(y.compareTo(BigInteger.ONE) != 0 && y.compareTo(n1) != 0) {
      var j = 1;
      while(j++ < k && y.compareTo(n1) != 0) {
        y = y.modPowInt(2,this);
        if(y.compareTo(BigInteger.ONE) == 0) return false;
      }
      if(y.compareTo(n1) != 0) return false;
    }
  }
  return true;
}

// protected
BigInteger.prototype.chunkSize = bnpChunkSize;
BigInteger.prototype.toRadix = bnpToRadix;
BigInteger.prototype.fromRadix = bnpFromRadix;
BigInteger.prototype.fromNumber = bnpFromNumber;
BigInteger.prototype.bitwiseTo = bnpBitwiseTo;
BigInteger.prototype.changeBit = bnpChangeBit;
BigInteger.prototype.addTo = bnpAddTo;
BigInteger.prototype.dMultiply = bnpDMultiply;
BigInteger.prototype.dAddOffset = bnpDAddOffset;
BigInteger.prototype.multiplyLowerTo = bnpMultiplyLowerTo;
BigInteger.prototype.multiplyUpperTo = bnpMultiplyUpperTo;
BigInteger.prototype.modInt = bnpModInt;
BigInteger.prototype.millerRabin = bnpMillerRabin;

// public
BigInteger.prototype.clone = bnClone;
BigInteger.prototype.intValue = bnIntValue;
BigInteger.prototype.byteValue = bnByteValue;
BigInteger.prototype.shortValue = bnShortValue;
BigInteger.prototype.signum = bnSigNum;
BigInteger.prototype.toByteArray = bnToByteArray;
BigInteger.prototype.equals = bnEquals;
BigInteger.prototype.min = bnMin;
BigInteger.prototype.max = bnMax;
BigInteger.prototype.and = bnAnd;
BigInteger.prototype.or = bnOr;
BigInteger.prototype.xor = bnXor;
BigInteger.prototype.andNot = bnAndNot;
BigInteger.prototype.not = bnNot;
BigInteger.prototype.shiftLeft = bnShiftLeft;
BigInteger.prototype.shiftRight = bnShiftRight;
BigInteger.prototype.getLowestSetBit = bnGetLowestSetBit;
BigInteger.prototype.bitCount = bnBitCount;
BigInteger.prototype.testBit = bnTestBit;
BigInteger.prototype.setBit = bnSetBit;
BigInteger.prototype.clearBit = bnClearBit;
BigInteger.prototype.flipBit = bnFlipBit;
BigInteger.prototype.add = bnAdd;
BigInteger.prototype.subtract = bnSubtract;
BigInteger.prototype.multiply = bnMultiply;
BigInteger.prototype.divide = bnDivide;
BigInteger.prototype.remainder = bnRemainder;
BigInteger.prototype.divideAndRemainder = bnDivideAndRemainder;
BigInteger.prototype.modPow = bnModPow;
BigInteger.prototype.modInverse = bnModInverse;
BigInteger.prototype.pow = bnPow;
BigInteger.prototype.gcd = bnGCD;
BigInteger.prototype.isProbablePrime = bnIsProbablePrime;

// BigInteger interfaces not implemented in jsbn:

// BigInteger(int signum, byte[] magnitude)
// double doubleValue()
// float floatValue()
// int hashCode()
// long longValue()
// static BigInteger valueOf(long val)


/* File: Templates/javascript/prng4.js */
/*prng4.js - uses Arcfour as a PRNG*/

 
function Arcfour() {
  this.i = 0;
  this.j = 0;
  this.S = new Array();
}

// Initialize arcfour context from key, an array of ints, each from [0..255]
function ARC4init(key) {
  var i, j, t;
  for(i = 0; i < 256; ++i)
    this.S[i] = i;
  j = 0;
  for(i = 0; i < 256; ++i) {
    j = (j + this.S[i] + key[i % key.length]) & 255;
    t = this.S[i];
    this.S[i] = this.S[j];
    this.S[j] = t;
  }
  this.i = 0;
  this.j = 0;
}

function ARC4next() {
  var t;
  this.i = (this.i + 1) & 255;
  this.j = (this.j + this.S[this.i]) & 255;
  t = this.S[this.i];
  this.S[this.i] = this.S[this.j];
  this.S[this.j] = t;
  return this.S[(t + this.S[this.i]) & 255];
}

Arcfour.prototype.init = ARC4init;
Arcfour.prototype.next = ARC4next;

// Plug in your RNG constructor here
function prng_newstate() {
  return new Arcfour();
}

// Pool size must be a multiple of 4 and greater than 32.
// An array of bytes the size of the pool will be passed to init()
var rng_psize = 256;


/* File: Templates/javascript/rng.js */
// Random number generator - requires a PRNG backend, e.g. prng4.js

// For best results, put code like
// <body onClick='rng_seed_time();' onKeyPress='rng_seed_time();'>
// in your main HTML document.


var rng_state;
var rng_pool;
var rng_pptr;

// Mix in a 32-bit integer into the pool
function rng_seed_int(x) {
  rng_pool[rng_pptr++] ^= x & 255;
  rng_pool[rng_pptr++] ^= (x >> 8) & 255;
  rng_pool[rng_pptr++] ^= (x >> 16) & 255;
  rng_pool[rng_pptr++] ^= (x >> 24) & 255;
  if(rng_pptr >= rng_psize) rng_pptr -= rng_psize;
  //alert("rng_psize: "+rng_psize);
}

// Mix in the current time (w/milliseconds) into the pool
function rng_seed_time() {
  rng_seed_int(new Date().getTime());
}

// Initialize the pool with junk if needed.
if(rng_pool == null) {
  
  rng_pool = new Array();
  rng_pptr = 0;
 
  var t;

  while(rng_pptr < rng_psize) {  // extract some randomness from Math.random()
    t = Math.floor(65536 * Math.random());
    rng_pool[rng_pptr++] = t >>> 8;
    rng_pool[rng_pptr++] = t & 255;
  }
  rng_pptr = 0;
  rng_seed_time();
  //rng_seed_int(window.screenX);
  //rng_seed_int(window.screenY);
}

function rng_get_byte() {
  if(rng_state == null) {
    rng_seed_time();
    rng_state = prng_newstate();
    rng_state.init(rng_pool);
    for(rng_pptr = 0; rng_pptr < rng_pool.length; ++rng_pptr)
      rng_pool[rng_pptr] = 0;
    rng_pptr = 0;
    //rng_pool = null;
  }
  // TODO: allow reseeding after first request
  return rng_state.next();
}

function rng_get_bytes(ba) {
  var i;
  for(i = 0; i < ba.length; ++i) ba[i] = rng_get_byte();
}

function SecureRandom() {}

SecureRandom.prototype.nextBytes = rng_get_bytes;


/* File: Templates/javascript/myxyz.js */
var url       = null;       //xyz servlet
var app_name    = '';
var initialized   = 0;
var debug       = false;  //don't submit login just show if it works or not
var XYZ         = true;   //use XYZ or fail to old authentication
var submit_form   = false;
var acct_id     = null;
var user_name     = null;
var password     = null;
var complete_authentication = false;
var complete_confirm_token = false;
var is_two_factor_user = false;
//pteng used to identify the user as second factor. used by WT to redirect to login on disconnect
var twoFactorUser = false;
var suppLongPwd = false;
var userSfTypes = [];
var selectedSF =null;

//default to 512 bit value
var N = parseBigInt("d4c7f8a2b32c11b8fba9581ec4ba4f1b04215642ef7355e37c0fc0443ef756ea2c6b8eeb755a1c723027663caa265ef785b8ff6a9b35227a52d86633dbdfca43",16);
var g = parseBigInt("2",10);
var a = null;
var A = null;
var B = null;
var k = null;
var x = null;
var u = null;
var K = null;
var M = 0;
var M2 = null;
var salt = null;
var rng = null;
var Sc = null;
var one;
var two;
var three;
var radix = 16;
var proto = "6";   // 3 or 6 or 6a
var hash  = "SHA1";

var startTime = null;  //measure time of execution start
var endTime = null;    //measure time of execution end

var INITIATED     = "INITIATED";     //starting authentication submitting username
var INITIALIZED   = "INITIALIZED";    //username submitted
var INPROCESS     = "INPROCESS";      //submitted M1
var AUTHENTICATED   = "AUTHENTICATED";   //allok
var FAILEDAUTH     = "FAILEDAUTH";      //failed
var STATE = null;
var NULL=null;  //<-- added
var twoFactType  = null;  //what type of two factor is used
var towFactChlg  = null;

var submit_enckx = false;

//PHONE AUTH VARIABLES
//3 minutes
//var PHONE_AUTH_POLLING_TIMEOUT = 180000;
var PUSH_AUTH_MAX_ATTEMPTS = 36;  //36*5s = 180s=3min
var PUSH_AUTH_ATTEMPTS = 0;
//5 seconds
var PUSH_CHECK_AUTH_INTERVAL = 5000
//POLLING URL
var PUSH_AUTH_POLLING_URL ='';
var PUSH_AUTH_STATE ='INVALID';
var PUSH_AUTH_INSTRUCTIONS = 'A message has been sent to your phone. Tap the link to complete secondary authentication.<br>';
var PUSH_AUTH_ALT_LINK = 'Click here if you did not receive the message.';
var PUSH_TIMEOUT_MSG = 'Error Two Factor Authentication Timed out.';

var pushTimeout;

var VERSION = 0;

//Local storage key
var SELECTED_SF_KEY="SELECTED_SF";
//URL param to reset LS
var RESET_KEY="resetSF";
//SF types
var SSC = "3";
var IBKEY_ANDROID = "5.2a";
var IBKEY_IOS = "5.2i";
var BANK_KEY = "5.3";
var DSC = "4.1";
var ALPINE = "4";
var DSC_PLUS = "5.1";
var PLAT_GOLD = "5";
var TSC = "6";
var SMS = "4.2"


var SF_NAMES ={};
SF_NAMES[SSC] = "Security Code Card";
SF_NAMES[IBKEY_ANDROID] = "IB Key";
SF_NAMES[IBKEY_IOS] = "IB Key";
SF_NAMES[BANK_KEY] = "Bank Key";
SF_NAMES[DSC] = "Digital Security Card";
SF_NAMES[ALPINE] = "Alpine Device";
SF_NAMES[DSC_PLUS] = "Digital Security Card+";
SF_NAMES[PLAT_GOLD] = "Platinum/Gold";
SF_NAMES[TSC] = "Temporary Security Code";
SF_NAMES[SMS] ="One Time Passcode"

var tempServerS2="";

IBSSO = {};
IBSSO.MESSAGES = {};
IBSSO.CONSTANT = {};

IBSSO.MESSAGES.LIVE_ACCOUNT_WITH_PAPER_TRADING = "You have selected the Live Account Mode, but the specified user is a Paper Trading user. Please select the correct Login mode.";
IBSSO.isPaper = {};

IBSSO.CONSTANT.LOGIN_TYPE_PROD = 1;
IBSSO.CONSTANT.LOGIN_TYPE_PAPER = 2;

IBSSO.CONSTANT.SECOND_FACTOR_TYPE_OTP = "4.2";
IBSSO.CONSTANT.OTP_DELIVERY_TYPE_SMS = 1;
IBSSO.CONSTANT.OTP_DELIVERY_TYPE_VOICE = 2;
IBSSO.CONSTANT.OTP_DELIVERY_TYPE_EMAIL = 4;

IBSSO.otpSelectTimer = null;
IBSSO.otpSelectTimerTimeout = 60 * 1000; //60sec


var loadingCallback = function(){
  //Quick check for url parameter to reset local store
  var resetSF = getParam(RESET_KEY);
  if(resetSF && resetSF=="true"){
    try {
      localStorage.setItem(SELECTED_SF_KEY, "");
    } catch(e) {}
  }
  if(typeof SF_VERSION != "undefined" && SF_VERSION){
    VERSION = SF_VERSION;
  }
};

var specialPushAuthRequest;
var specialCompleteAuth_1;

//ibkey recovery variables

var MODE_NORMAL = "NORMAL";
var MODE_IBKEY_RECOVERY = "IBKEY_RECOVERY";
var MODE = MODE_NORMAL;

function isync_radix() {
  radix = 16;
}

function isync_proto() {
  proto = "6";
}



function bigInt2radix(bi, radix){
  return bi.toString(radix);
}

function randomBigInt(bytes) {
  if(rng == null) {
    rng = new SecureRandom();
  }
  return new BigInteger(8 * bytes, rng);
}

function str2BigInt(str) {
  return parseBigInt(str, radix);
}

function bigInt2Str(bi) {
  return bigInt2radix(bi, radix);
}

/* Returns a string with n zeroes in it */
function nzero(n) {
  if(n < 1) {
    return "";
  }
  var t = nzero(n >> 1);
  if((n & 1) == 0) {
    return t + t;
  }
  else {
    return t + t + "0";
  }
}

function set_random_a() {
  a = randomBigInt(32);
  if(a.compareTo(N) >= 0) {
    a = a.mod(N.subtract(one));
  }
  if(a.compareTo(two) < 0) {
    a = two;
  }
  //for tests keep it static
  // a = parseBigInt("222444666",16);
}

function randomize_a() {
  set_random_a();
  recalc_A();
}

function recalc_A() {
  A = g.modPow(a, N);
}

function recalc_k() {
  k = xyz_compute_k(N, g);
}

function recalc_K() {
  console.log(Sc);
 // writeDebug("recalc_K Sc = "+bigInt2radix(Sc,16));
  K = xyz_compute_K(Sc);
  console.log(K);
 // writeDebug("recalc_K K = "+K);
}

function recalc_M() {
  M = xyz_compute_M1(N, g,user_name, salt, A, B, K);
  return M
 // writeDebug("recalc_M M = "+M);
}

function recalc_M2(){
  M2 = xyz_compute_M2(A,M,K);
}

function recalc_x() {
 // writeDebug("recalc_x  user = "+getUserName());
 // writeDebug("recalc_x  pass = "+getPassword());
 // writeDebug("recalc_x  salt = "+bigInt2radix(salt,16));
  x = xyz_compute_x(user_name, password, salt);
 // writeDebug("recalc_x x = "+bigInt2radix(x ,16));
}

function recalc_Sc() {
 // writeDebug("recalc_Sc B = "+bigInt2radix(B, 16));
 // writeDebug("recalc_Sc x = "+bigInt2radix(x, 16));
 // writeDebug("recalc_Sc u = "+bigInt2radix(u, 16));
 // writeDebug("recalc_Sc a = "+bigInt2radix(a, 16));
 // writeDebug("recalc_Sc k = "+bigInt2radix(k, 16));
  Sc = xyz_compute_client_S(B, x, u, a, k);
 // writeDebug("recalc_Sc Sc = "+bigInt2radix(Sc, 16));
}

function recalc_u() {
 // writeDebug("recalc_u N = "+bigInt2radix(N,16));
 // writeDebug("recalc_u A = "+bigInt2radix(A, 16));
 // writeDebug("recalc_u B = "+bigInt2radix(B, 16));
  u = xyz_compute_u(N, A, B);
 // writeDebug("recalc_u u = "+u);
}

function recalc_v(){
  // writeDebug("recalc_v g = "+g);
  // writeDebug("recalc_v x = "+x);
   var v = xyz_compute_v(g,x);
  // writeDebug("recalc_v v = "+v);
}

/* S = (B - kg^x) ^ (a + ux) (mod N) */
function xyz_compute_client_S(BB, xx, uu, aa, kk) {
  var bx = g.modPow(xx, N);
  console.log("xyz_compute_client_S")
  console.log(BB);
  console.log(N);
  console.log(kk);
  var btmp = BB.add(N.multiply(kk)).subtract(bx.multiply(kk)).mod(N);
  return btmp.modPow(xx.multiply(uu).add(aa), N);
}

function xyz_compute_k(NN, gg) {
  var hashin = "";
  var nhex;
  var ghex;
  var ktmp;
  if(proto == "3")
    return one;
  else if(proto == "6")
    return three;
  else {
    /* XYZ-6a: k = H(N || g) */
    nhex = String(bigInt2radix(NN, 16));
    if((nhex.length & 1) == 0) {
      hashin += nhex;
    }
    else {
      hashin += "0" + nhex;
    }
    ghex = String(bigInt2radix(gg, 16));
    hashin += nzero(nhex.length - ghex.length);
    hashin += ghex;
    ktmp = parseBigInt(calcSHA1Hex(hashin), 16);
    if(ktmp.compareTo(NN) < 0) {
      return ktmp;
    }
    else {
      return ktmp.mod(NN);
    }
  }
}

/* x = H(salt || H(username || ":" || password)) */
function xyz_compute_x(u, p, s) {
  // Inner hash: SHA-1(username || ":" || password)
  var ih = calcSHA1(u + ":" + p);
  // Outer hash: SHA-1(salt || inner_hash)
  // This assumes that the hex salt string has an even number of characters...
  //original
  //var oh = calcSHA1Hex(bigInt2radix(s, 16) + ih);
  //this makes sure that hex salt string has an even number of characters, kt ...
   var oh = calcSHA1Hex(verifyHexVal(s) + ih);
  var xtmp = parseBigInt(oh, 16);
  if(xtmp.compareTo(N) < 0) {
    return xtmp;
  }
  else {
    return xtmp.mod(N.subtract(one));
  }
}

/*
 * XYZ-3: u = first 32 bits (MSB) of SHA-1(B)
 * XYZ-6(a): u = SHA-1(A || B)
 */

function xyz_compute_u(Nv, av, bv) {
  var ahex;
  var bhex = String(bigInt2radix(bv, 16));
  var hashin = "";
  var utmp;
  var nlen;
  if(proto != "3") {
    ahex = String(bigInt2radix(av, 16));
    if(proto == "6") {
      if((ahex.length & 1) == 0) {
        hashin += ahex;
      }
      else {
        hashin += "0" + ahex;
      }
    }
    else { /* 6a requires left-padding */
      nlen = 2 * ((Nv.bitLength() + 7) >> 3);
      hashin += nzero(nlen - ahex.length) + ahex;
    }
  }
  if(proto == "3" || proto == "6") {
    if((bhex.length & 1) == 0) {
      hashin += bhex;
    }
    else {
      hashin += "0" + bhex;
    }
  }
  else { /* 6a requires left-padding; nlen already set above */
    hashin += nzero(nlen - bhex.length) + bhex;
  }
  if(proto == "3") {
    utmp = parseBigInt(calcSHA1Hex(hashin).substr(0, 8), 16);
  }
  else {

    utmp = parseBigInt(calcSHA1Hex(hashin), 16);
  }
  if(utmp.compareTo(Nv) < 0) {
    return utmp;
  }
  else {
    return utmp.mod(Nv.subtract(one));
  }
}

/* K = H(S) */
function xyz_compute_K(SS) {
  var tmpk = calcSHA1Hex(verifyHexVal(SS));
  // writeDebug("xyz_compute_K K = "+tmpk);
  return tmpk;
}

// M = H(A,B,K) */
function xyz_compute_M_old(AI,BI,KI) {
  var hashin ="";
  hashin +=  String(bigInt2radix(verifyHexVal(AI), 16));
  hashin +=  String(bigInt2radix(verifyHexVal(BI), 16));
  hashin +=  String(bigInt2radix(verifyHexVal(KI), 16));

  return calcSHA1Hex(hashin);
}

// M1 = H( H(N) xor H(g), H(I), s, A,B,K) */
function xyz_compute_M1(NI, gI, uI, sI, AI,BI,KI) {
  var hashin ="";
  //  writeDebug("xyz_compute_M1 N: "+NI);
  var h_n = calcSHA1Hex(bigInt2radix(verifyHexVal(NI), 16));
  // writeDebug("xyz_compute_M1 h_n: "+h_n);
  //  writeDebug("xyz_compute_M1 g: "+gI);

  var h_g = calcSHA1Hex(bigInt2radix(verifyHexVal(gI), 16));
  // writeDebug("xyz_compute_M1 h_g: "+h_g);
  h_n = parseBigInt(verifyHexVal(h_n), 16);
  h_g = parseBigInt(verifyHexVal(h_g), 16);

  var h_xor = verifyHexVal(bigInt2radix(h_n.xor(h_g),16));
  // writeDebug("xyz_compute_M1 xor: "+h_xor);

  // writeDebug("xyz_compute_M1 username: "+uI);
  var h_I = calcSHA1(uI);
  // writeDebug("xyz_compute_M1 h_I: "+h_I);

  var shex =  verifyHexVal(sI);
  // writeDebug("xyz_compute_M1 s_hex: "+shex);
  // writeDebug("xyz_compute_M1 AI : "+bigInt2radix(verifyHexVal(AI), 16));
  // writeDebug("xyz_compute_M1 BI : "+bigInt2radix(verifyHexVal(BI), 16));
  // writeDebug("xyz_compute_M1 KI : "+bigInt2radix(verifyHexVal(KI), 16));

  hashin +=  h_xor;
  hashin +=  h_I;
  hashin +=  shex;
  hashin +=  String(bigInt2radix(verifyHexVal(AI), 16));
  hashin +=  String(bigInt2radix(verifyHexVal(BI), 16));
  hashin +=  String(bigInt2radix(verifyHexVal(KI), 16));
  // writeDebug("xyz_compute_M1 hashin= "+hashin);
  return verifyHexVal(calcSHA1Hex(hashin));
}

function xyz_compute_M2(AI,MI,KI) {
  //alert("A: "+AI+"\nMI: "+MI+"\nKI: "+KI);
  var hashin ="";
  hashin +=  String(bigInt2radix(verifyHexVal(AI), 16));
  hashin +=  String(bigInt2radix(verifyHexVal(MI), 16));
  hashin +=  String(bigInt2radix(verifyHexVal(KI), 16));

  return calcSHA1Hex(hashin);
}

/* v = g^x */
function xyz_compute_v(gi, xi) {
 return gi.modPow(xi, N);
}

/* this makes sure it is even number  */
function verifyHexVal(HV){
  var hashin ="";
  var bhex = String(bigInt2radix(HV, 16));
  if((bhex.length & 1) == 0) {
    hashin += bhex;
  }
  else {
    hashin += "0" + bhex;
  }

  //20061106
  if(hashin.charAt(0) == "0" && hashin.charAt(1) == "0"){
    hashin = hashin.substring(2,hashin.length);
  }
  return hashin;
}

function set_radix(r) {
  radix = r;
}

function set_proto(p) {
  proto = p;
  recalc_k();
}


function xyz_initialize() {
  rng_seed_time();
  if(initialized > 0)
  {
    return;
  }
  one = parseBigInt("1", 16);
  two = parseBigInt("2", 16);
  three = parseBigInt("3", 16);

  randomize_a();
  console.log("A VALUES:")
  console.log(a);
  console.log(A);
  console.log(B);
  initialized = 1;

  AA = parseBigInt(A.toString(), 16)
  p = {
    "a": a.toString(),
    "A2": A.toString(),
    "A": bigInt2Str(A),
  }
  return p
}

function get_A(){
  return A.toString();
}

var userNameFocused = false;
var passwordFocused = false;
var forceUserNameFocused = false;
var forcePasswordFocused = false;
var userNameEnterPressed = false;


/* File: Templates/javascript/rsa.js */
// Depends on jsbn.js and rng.js

// convert a (hex) string to a bignum object
function parseBigInt(str,r) {
  return new BigInteger(str,r);
}

function linebrk(s,n) {
  var ret = "";
  var i = 0;
  while(i + n < s.length) {
    ret += s.substring(i,i+n) + "\n";
    i += n;
  }
  return ret + s.substring(i,s.length);
}

function byte2Hex(b) {
  if(b < 0x10)
    return "0" + b.toString(16);
  else
    return b.toString(16);
}

// PKCS#1 (type 2, random) pad input string s to n bytes, and return a bigint
function pkcs1pad2(s,n) {
  if(n < s.length + 11) {
    alert("Message too long for RSA");
    return null;
  }
  var ba = new Array();
  var i = s.length - 1;
  while(i >= 0 && n > 0) ba[--n] = s.charCodeAt(i--);
  ba[--n] = 0;
  var rng = new SecureRandom();
  var x = new Array();
  while(n > 2) { // random non-zero pad
    x[0] = 0;
    while(x[0] == 0) rng.nextBytes(x);
    ba[--n] = x[0];
  }
  ba[--n] = 2;
  ba[--n] = 0;
  return new BigInteger(ba);
}

// "empty" RSA key constructor
function RSAKey() {
  this.n = null;
  this.e = 0;
  this.d = null;
  this.p = null;
  this.q = null;
  this.dmp1 = null;
  this.dmq1 = null;
  this.coeff = null;
}

// Set the public key fields N and e from hex strings
function RSASetPublic(N,E) {
  if(N != null && E != null && N.length > 0 && E.length > 0) {
    this.n = parseBigInt(N,16);
    this.e = parseInt(E,16);
  }
  else
    alert("Invalid RSA public key");
}

// Perform raw public operation on "x": return x^e (mod n)
function RSADoPublic(x) {
  return x.modPowInt(this.e, this.n);
}

// Return the PKCS#1 RSA encryption of "text" as an even-length hex string
function RSAEncrypt(text) {
  var m = pkcs1pad2(text,(this.n.bitLength()+7)>>3);
  if(m == null) return null;
  var c = this.doPublic(m);
  if(c == null) return null;
  var h = c.toString(16);
  if((h.length & 1) == 0) return h; else return "0" + h;
}

// Return the PKCS#1 RSA encryption of "text" as a Base64-encoded string
//function RSAEncryptB64(text) {
//  var h = this.encrypt(text);
//  if(h) return hex2b64(h); else return null;
//}

// protected
RSAKey.prototype.doPublic = RSADoPublic;

// public
RSAKey.prototype.setPublic = RSASetPublic;
RSAKey.prototype.encrypt = RSAEncrypt;
//RSAKey.prototype.encrypt_b64 = RSAEncryptB64;


/* File: Templates/javascript/base64.js */
var b64map="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
var b64pad="=";

function hex2b64(h) {
  var i;
  var c;
  var ret = "";
  for(i = 0; i+3 <= h.length; i+=3) {
    c = parseInt(h.substring(i,i+3),16);
    ret += b64map.charAt(c >> 6) + b64map.charAt(c & 63);
  }
  if(i+1 == h.length) {
    c = parseInt(h.substring(i,i+1),16);
    ret += b64map.charAt(c << 2);
  }
  else if(i+2 == h.length) {
    c = parseInt(h.substring(i,i+2),16);
    ret += b64map.charAt(c >> 2) + b64map.charAt((c & 3) << 4);
  }
  while((ret.length & 3) > 0) ret += b64pad;
  return ret;
}

// convert a base64 string to hex
function b64tohex(s) {
  var ret = "";
  var i;
  var k = 0; // b64 state, 0-3
  var slop;
  for(i = 0; i < s.length; ++i) {
    if(s.charAt(i) == b64pad) break;
    v = b64map.indexOf(s.charAt(i));
    if(v < 0) continue;
    if(k == 0) {
      ret += int2char(v >> 2);
      slop = v & 3;
      k = 1;
    }
    else if(k == 1) {
      ret += int2char((slop << 2) | (v >> 4));
      slop = v & 0xf;
      k = 2;
    }
    else if(k == 2) {
      ret += int2char(slop);
      ret += int2char(v >> 2);
      slop = v & 3;
      k = 3;
    }
    else {
      ret += int2char((slop << 2) | (v >> 4));
      ret += int2char(v & 0xf);
      k = 0;
    }
  }
  if(k == 1)
    ret += int2char(slop << 2);
  return ret;
}

// convert a base64 string to a byte/number array
function b64toBA(s) {
  //piggyback on b64tohex for now, optimize later
  var h = b64tohex(s);
  var i;
  var a = new Array();
  for(i = 0; 2*i < h.length; ++i) {
    a[i] = parseInt(h.substring(2*i,2*i+2),16);
  }
  return a;
}


/* File: Templates/javascript/encr.js */
var e = "3";
var pubKey = null;
var rsa = null;



function do_encrypt(ptext) {

  var res = rsa.encrypt(ptext);
  return res;
}

function get_EKX(rsapub) {
    rsa = new  RSAKey();
    rsa.setPublic(rsapub,'3');
    console.log(K);
  var ekx = do_encrypt(K);
  return ekx;
}


/*
function do_encrypt_with_form(ptext) {

  var res = do_encrypt(ptext);
  var after = new Date();
  if(res) {
   // alert(ptext);
    var input = document.createElement("input");
    input.type = "hidden";
    input.name = "epass";
    input.id = "epass";
    input.value = res;

    var form = document.getElementById("newuserini");
    form.appendChild(input);


    var after = new Date();
    ptext.value = "";
    return true;
   // alert(before+"\n"+after);
  }
  return false;
}
*/

function compute_sk(seed,verifier) {
  var hashin ="";
  hashin +=  String(bigInt2radix(verifyHexVal(seed), 16));
  hashin +=  String(bigInt2radix(verifyHexVal(verifier), 16));
  var ret = calcSHA1Hex(hashin);

  return ret;
}

function second_step(u, p, s, bb, rsapub, aa, AA) {
  user_name = u
  password = p
  N = "d4c7f8a2b32c11b8fba9581ec4ba4f1b04215642ef7355e37c0fc0443ef756ea2c6b8eeb755a1c723027663caa265ef785b8ff6a9b35227a52d86633dbdfca43"
  N = parseBigInt(N, 16)

  a = new BigInteger(aa)
  recalc_A()
  //A = parseBigInt(AA, 16)

  salt = parseBigInt(s, 16)
  B = parseBigInt(bb, 16)

  recalc_k();

  recalc_x();
  recalc_u();
  recalc_Sc();
  recalc_K();
  M1 = recalc_M()
  ekx = get_EKX(rsapub)

  recalc_M2()
  sk = compute_sk(B,K)
  return {"M1": M1, 'EKX': ekx, 'A': A.toString(), 'AA': bigInt2Str(A), 'K': K, 'sk': sk, 'M2': M2}
}

one = parseBigInt("1", 16);
two = parseBigInt("2", 16);
three = parseBigInt("3", 16);
if (false) {
  //p = xyz_initialize()
  //a = p['a']
  //A = p['A']

  A = "3056784236776875126107998772595822140992024391549546753081784170654756236308913169544852699092148732318348837003859861031918719477032412494302463140899815"
  a = "31798882676495148259456991604878405597502690924142754157115361047479678328178"
  rsa_pub = "A0EC24D9D02F8AB5F78AA415915F6CC0FCB6919E9BDEB75B1C180381CAD3DA5C8B74798CFB19B9F5E24489AC55059658D99A74CD5143C01ED3F889E4B23EF7EFD61D54DA85C769E8308C1D96762F0FC50AC8D2B06C4DC64B858FB14430077F16F6F39113786CDA131FAFCAEA90E2C4E06E7C1066A97EB371DA9A4B812378B4F9"
  bb = "bed3821333b13a62981817ce34397f73f1dfcd00393cabb2da95096226f0215a31b4982f7f17e56a5f5c73b952b3061dab7d27a89e9353642377fe6454626caf"
  // A = "4372026559445453341485862456644265281052589330447146217290896860792097719861049755854419902615971152734065987202648550192873370672792119383604247981920897"
  qw = second_step("user", "pas", "866b5c4c", bb, rsa_pub, A, a)
  //get_EKX()
}

function new_recalcU(N, A, B) {
  B = parseBigInt(B,16);
  N = parseBigInt(N, 16);
  // a = new BigInteger(aa)
  // recalc_A()
  A = parseBigInt(A,16)
  //N = parseBigInt(N,16)
  return xyz_compute_u(N, A, B).toString();
}

function simulate_working(){
  a = "26473844128524228113794185652668423832647437522406158068359080410988633429062" // toString()
  //a2 = "414d18abaf99e2a9b9c9ac831fe8c9563432e89c94173b06eb8561552e1aa617"
  //A = "79d27ba07e7a63b20a437dd4a807acdf0f723cd331f5678f08addc5d0fe7774f54a8c055f4176e0c10f8295a5cc8019553d3a29bffdf0ec8f492b697ef65d8f9"
  N = "d4c7f8a2b32c11b8fba9581ec4ba4f1b04215642ef7355e37c0fc0443ef756ea2c6b8eeb755a1c723027663caa265ef785b8ff6a9b35227a52d86633dbdfca43"
  B = "48cff39757ce1b99cc57bf7bb75480d1ec64a73ff05f4e7575b67ba56e76f439e37768b297eddf147fce93c2c8108922eef437a32dadd9799d5bd947f3e5681c"
  salt = "866b5c4c"
  rsapub = "AF281D1BDAEA6474AAF6D7DE6030B21961382FAE1197C96F99C48C9D4CCD9F3DFFF57006D0E7AE27CD7B4F35A7B01FB6C9C5F38868AE596DFDBFBCC94D450F7D2A33767E3067A72B071E7D1DFF9CFAC3286133B8258360F93169624B054378D7A77D25B4995192520C56B23635AB73DE704C5EF9FE7E8CA6EC74D5A6A8B39B4B"

  M1_should_be = "b1ce802b583acd1fcd697f7d2cc64214b430120b"
  EKX_should_be = "3de3fe38b91c04a04a891f377fd69adcd2857f00dc51ee968f406b0c3f03dea0a15ff7316d803ffac724814d6f618166cd2410259cb8055843758a0c60dc50de878a3c80c828bf749f41ec33d2ee0afd81b789ceeeb8aadae4e51a92bafc386ad84647107eeb01660b215720900cdeaa3e4c737103b95b869378845b38e473ec"

  user_name = "";
  password = "";
  B = parseBigInt(B, 16)
  N = parseBigInt(N, 16)

  a = new BigInteger(a)
  // a = parseBigInt(a2, 16)
  recalc_A()

  // A = parseBigInt(A, 16)
  salt = parseBigInt(salt, 16)

  recalc_k();

  recalc_x();
  recalc_u();
  recalc_Sc();
  recalc_K();
  M1 = recalc_M()
  ekx = get_EKX(rsapub)


  rsa2 = new RSAKey();
  rsa2.setPublic(rsapub, '3')
  extra_calc = rsa2.encrypt("10a0c741f6bce2459777213a516f38884d25f2a6");

  return {"M1": M1, 'EKX': ekx, 'A': A.toString(), 'AA': bigInt2Str(A), 'extra_calc': extra_calc,
    'K': K, 'M1_should_be': M1_should_be, 'EKX_should_be': EKX_should_be,
  'a': a.toString(), 'a2': bigInt2Str(a),
  'B': B.toString(), 'B2': bigInt2Str(B),
  'N': N.toString(), 'N2': bigInt2Str(B),
  'k': k.toString(), 'k2': bigInt2Str(k),
  'K': K.toString(), 'K2': bigInt2Str(K)}
}

function simulate_working2(){


  a = "102599583269301484255675206705244778480624302455415109851056649396815895425679"
 A2 = "11135629485709523893655286323728802426310595170655272892183999328283454603049075789984565277122377602030744145960285836852836508138644814415716811309149752"
 A = "d49dd2b79c1ebefc84318ff4c9e20d15a39a9cd51111429ed349d666c019388f0e76b6006eb2dbdb7964f22ce6bda35a297e27098d4f360d6f483d3535b56e38"
 M1= "e548a54364d6c7c685df334ea9b383baef29bdcb"
 EKX = "9481c6a3184ce78793e98bc3abb45028e2a1b7760a483bdee97b6012c6c2b4028cb23d23c9615fb04a48282c4bf120b34835f495673d7d9b8a329430a0d6c7131424f3906b4e35cde9cc3a03d0c68471363d823ab9cd915c423aa7bfbe16ab48c0962cc53d3150a90e6b688f748284eaa8a5bf064e2720bcce4201123714d931"
 A = "11135629485709523893655286323728802426310595170655272892183999328283454603049075789984565277122377602030744145960285836852836508138644814415716811309149752"
 AA = "d49dd2b79c1ebefc84318ff4c9e20d15a39a9cd51111429ed349d666c019388f0e76b6006eb2dbdb7964f22ce6bda35a297e27098d4f360d6f483d3535b56e38"
 K = "2374f9fed75fd8276a20851ae1cbdeedd08b157e"
B = 'a5d475f8267310af86790574949624082f30faaf968347088f625166b40d59438c1d0f68d8bf2a0c3c16bace3a6a6134d348de81e075386d6186ed6039b22bf5'
  rsapub = "A1292294D39D10AA61EA93CB17ACC4E0755FA8CE07D79EE3F9EA8520EFAD199965705AAE66FAF485BD741866691A20E6C74C56590B5B7D0D1800960F6C7613E312795BC5E75812F8EC834F7F5A44E43700D2D3DC68226706A9D3D4F5BE066F0125A95038736B890D0E4F89324095C9F3090994806C8B6269DAC6D3441DB029AF"
    user_name = ""
  password = ""
  B = parseBigInt(B, 16)
  //N = parseBigInt(N, 16)
    a = new BigInteger(a)
    recalc_A()
  salt = parseBigInt(salt, 16)
    recalc_k();

  recalc_x();
  recalc_u();
  recalc_Sc();
  recalc_K();
  M1 = recalc_M()
  ekx = get_EKX(rsapub)

  return {"M1": M1, 'EKX': ekx, 'A': A.toString(), 'AA': bigInt2Str(A),
    'K': K,   'a': a.toString(), 'a2': bigInt2Str(a),
  'B': B.toString(), 'B2': bigInt2Str(B),
  'N': N.toString(), 'N2': bigInt2Str(B),
  'k': k.toString(), 'k2': bigInt2Str(k),
  'K': K.toString(), 'K2': bigInt2Str(K)}
}