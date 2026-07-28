(function(){"use strict";/*! js-cookie v3.0.5 | MIT */function B(e){for(var o=1;o<arguments.length;o++){var t=arguments[o];for(var c in t)e[c]=t[c]}return e}var re={read:function(e){return e[0]==='"'&&(e=e.slice(1,-1)),e.replace(/(%[\dA-F]{2})+/gi,decodeURIComponent)},write:function(e){return encodeURIComponent(e).replace(/%(2[346BF]|3[AC-F]|40|5[BDE]|60|7[BCD])/g,decodeURIComponent)}};function T(e,o){function t(r,n,u){if(!(typeof document>"u")){u=B({},o,u),typeof u.expires=="number"&&(u.expires=new Date(Date.now()+u.expires*864e5)),u.expires&&(u.expires=u.expires.toUTCString()),r=encodeURIComponent(r).replace(/%(2[346B]|5E|60|7C)/g,decodeURIComponent).replace(/[()]/g,escape);var i="";for(var h in u)u[h]&&(i+="; "+h,u[h]!==!0&&(i+="="+u[h].split(";")[0]));return document.cookie=r+"="+e.write(n,r)+i}}function c(r){if(!(typeof document>"u"||arguments.length&&!r)){for(var n=document.cookie?document.cookie.split("; "):[],u={},i=0;i<n.length;i++){var h=n[i].split("="),s=h.slice(1).join("=");try{var a=decodeURIComponent(h[0]);if(u[a]=e.read(s,a),r===a)break}catch{}}return r?u[r]:u}}return Object.create({set:t,get:c,remove:function(r,n){t(r,"",B({},n,{expires:-1}))},withAttributes:function(r){return T(this.converter,B({},this.attributes,r))},withConverter:function(r){return T(B({},this.converter,r),this.attributes)}},{attributes:{value:Object.freeze(o)},converter:{value:Object.freeze(e)}})}var x=T(re,{path:"/"});const ae=`
:root {
  --b-100: #F2F3F7;
  --s-700: #37546D;
}

.woot-widget-holder {
  box-shadow: 0 5px 40px rgba(0, 0, 0, .16);
  opacity: 1;
  will-change: transform, opacity;
  transform: translateY(0);
  overflow: hidden !important;
  position: fixed !important;
  transition: opacity 0.2s linear, transform 0.25s linear;
  z-index: 2147483000 !important;
}

.woot-widget-holder.woot-widget-holder--flat {
  box-shadow: none;
  border-radius: 0;
  border: 1px solid var(--b-100);
}

.woot-widget-holder iframe {
  border: 0;
  color-scheme: normal;
  height: 100% !important;
  width: 100% !important;
  max-height: 100vh !important;
}

.woot-widget-holder.has-unread-view {
  border-radius: 0 !important;
  min-height: 80px !important;
  height: auto;
  bottom: 94px;
  box-shadow: none !important;
  border: 0;
}

.woot-widget-bubble {
  background: #1f93ff;
  border-radius: 100px;
  border-width: 0px;
  bottom: 20px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, .16) !important;
  cursor: pointer;
  height: 64px;
  padding: 0px;
  position: fixed;
  user-select: none;
  width: 64px;
  z-index: 2147483000 !important;
  overflow: hidden;
}

.woot-widget-bubble.woot-widget-bubble--flat {
  border-radius: 0;
}

.woot-widget-holder.woot-widget-holder--flat {
  bottom: 90px;
}

.woot-widget-bubble.woot-widget-bubble--flat {
  height: 56px;
  width: 56px;
}

.woot-widget-bubble.woot-widget-bubble--flat svg {
  margin: 16px;
}

.woot-widget-bubble.woot-widget-bubble--flat.woot--close::before,
.woot-widget-bubble.woot-widget-bubble--flat.woot--close::after {
  left: 28px;
  top: 16px;
}

.woot-widget-bubble.unread-notification::after {
  content: '';
  position: absolute;
  width: 12px;
  height: 12px;
  background: #ff4040;
  border-radius: 100%;
  top: 0px;
  right: 0px;
  border: 2px solid #ffffff;
  transition: background 0.2s ease;
}

.woot-widget-bubble.woot-widget--expanded {
  bottom: 24px;
  display: flex;
  height: 48px !important;
  width: auto !important;
  align-items: center;
}

.woot-widget-bubble.woot-widget--expanded div {
  align-items: center;
  color: #fff;
  display: flex;
  font-family: system-ui, -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Oxygen-Sans, Ubuntu, Cantarell, Helvetica Neue, Arial, sans-serif;
  font-size: 16px;
  font-weight: 500;
  justify-content: center;
  padding-right: 20px;
  width: auto !important;
}

.woot-widget-bubble.woot-widget--expanded.woot-widget-bubble-color--lighter div{
  color: var(--s-700);
}

.woot-widget-bubble.woot-widget--expanded svg {
  height: 20px;
  margin: 14px 8px 14px 16px;
  width: 20px;
}

.woot-widget-bubble.woot-elements--left {
  left: 20px;
}

.woot-widget-bubble.woot-elements--right {
  right: 20px;
}

.woot-widget-bubble:hover {
  background: #1f93ff;
  box-shadow: 0 8px 32px rgba(0, 0, 0, .4) !important;
}

.woot-widget-bubble svg {
  all: revert;
  height: 24px;
  margin: 20px;
  width: 24px;
}

.woot-widget-bubble.woot-widget-bubble-color--lighter path{
  fill: var(--s-700);
}

@media only screen and (min-width: 667px) {
  .woot-widget-holder.woot-elements--left {
    left: 20px;
 }
  .woot-widget-holder.woot-elements--right {
    right: 20px;
 }
}

.woot--close:hover {
  opacity: 1;
}

.woot--close::before, .woot--close::after {
  background-color: #fff;
  content: ' ';
  display: inline;
  height: 24px;
  left: 32px;
  position: absolute;
  top: 20px;
  width: 2px;
}

.woot-widget-bubble-color--lighter.woot--close::before, .woot-widget-bubble-color--lighter.woot--close::after {
  background-color: var(--s-700);
}

.woot--close::before {
  transform: rotate(45deg);
}

.woot--close::after {
  transform: rotate(-45deg);
}

.woot--hide {
  bottom: -100vh !important;
  top: unset !important;
  opacity: 0;
  visibility: hidden !important;
  z-index: -1 !important;
}

.woot-widget--without-bubble {
  bottom: 20px !important;
}
.woot-widget-holder.woot--hide{
  transform: translateY(40px);
}
.woot-widget-bubble.woot--close {
  transform: translateX(0px) scale(1) rotate(0deg);
  transition: transform 300ms ease, opacity 100ms ease, visibility 0ms linear 0ms, bottom 0ms linear 0ms;
}
.woot-widget-bubble.woot--close.woot--hide {
  transform: translateX(8px) scale(.75) rotate(45deg);
  transition: transform 300ms ease, opacity 200ms ease, visibility 0ms linear 500ms, bottom 0ms ease 200ms;
}

.woot-widget-bubble {
  transform-origin: center;
  will-change: transform, opacity;
  transform: translateX(0) scale(1) rotate(0deg);
  transition: transform 300ms ease, opacity 100ms ease, visibility 0ms linear 0ms, bottom 0ms linear 0ms;
}
.woot-widget-bubble.woot--hide {
  transform: translateX(8px) scale(.75) rotate(-30deg);
  transition: transform 300ms ease, opacity 200ms ease, visibility 0ms linear 500ms, bottom 0ms ease 200ms;
}

.woot-widget-bubble.woot-widget--expanded {
  transform: translateX(0px);
  transition: transform 300ms ease, opacity 100ms ease, visibility 0ms linear 0ms, bottom 0ms linear 0ms;
}
.woot-widget-bubble.woot-widget--expanded.woot--hide {
  transform: translateX(8px);
  transition: transform 300ms ease, opacity 200ms ease, visibility 0ms linear 500ms, bottom 0ms ease 200ms;
}
.woot-widget-bubble.woot-widget-bubble--flat.woot--close {
  transform: translateX(0px);
  transition: transform 300ms ease, opacity 10ms ease, visibility 0ms linear 0ms, bottom 0ms linear 0ms;
}
.woot-widget-bubble.woot-widget-bubble--flat.woot--close.woot--hide {
  transform: translateX(8px);
  transition: transform 300ms ease, opacity 200ms ease, visibility 0ms linear 500ms, bottom 0ms ease 200ms;
}
.woot-widget-bubble.woot-widget--expanded.woot-widget-bubble--flat {
  transform: translateX(0px);
  transition: transform 300ms ease, opacity 200ms ease, visibility 0ms linear 0ms, bottom 0ms linear 0ms;
}
.woot-widget-bubble.woot-widget--expanded.woot-widget-bubble--flat.woot--hide {
  transform: translateX(8px);
  transition: transform 300ms ease, opacity 200ms ease, visibility 0ms linear 500ms, bottom 0ms ease 200ms;
}

@media only screen and (max-width: 667px) {
  .woot-widget-holder {
    height: 100%;
    right: 0;
    top: 0;
    width: 100%;
 }

 .woot-widget-holder iframe {
    min-height: 100% !important;
  }


 .woot-widget-holder.has-unread-view {
    height: auto;
    right: 0;
    width: auto;
    bottom: 0;
    top: auto;
    max-height: 100vh;
    padding: 0 8px;
  }

  .woot-widget-holder.has-unread-view iframe {
    min-height: unset !important;
  }

 .woot-widget-holder.has-unread-view.woot-elements--left {
    left: 0;
  }

  .woot-widget-bubble.woot--close {
    bottom: 60px;
    opacity: 0;
    visibility: hidden !important;
    z-index: -1 !important;
  }
}

@media only screen and (min-width: 667px) {
  .woot-widget-holder {
    border-radius: 16px;
    bottom: 104px;
    height: calc(90% - 64px - 20px);
    max-height: 640px !important;
    min-height: 250px !important;
    width: 400px !important;
 }
}

.woot-hidden {
  display: none !important;
}
`,se=()=>{const e=document.createElement("style");e.innerHTML=`${ae}`,e.id="cw-widget-styles",e.dataset.turboPermanent=!0,document.body.appendChild(e)},M=(e,o)=>{const t=document.getElementById(e),c=o.querySelector(`#${e}`);t&&!c&&o.appendChild(t)},F=e=>{M("cw-bubble-holder",e),M("cw-widget-holder",e),M("cw-widget-styles",e)},y=(e,o)=>{e.classList.add(...o.split(" "))},k=(e,o)=>{e.classList.toggle(o)},_=(e,o)=>{e.classList.remove(...o.split(" "))},W=({referrerURL:e,referrerHost:o})=>{g.events.onLocationChange({referrerURL:e,referrerHost:o})},le=()=>{let e=document.location.href;const o=document.location.host,t={childList:!0,subtree:!0};W({referrerURL:e,referrerHost:o});const c=document.querySelector("body");new MutationObserver(n=>{n.forEach(()=>{e!==document.location.href&&(e=document.location.href,W({referrerURL:e,referrerHost:o}))})}).observe(c,t)},A=["standard","expanded_bubble"],P=["standard","flat"],q=["light","auto","dark"],z=e=>A.includes(e)?e:A[0],j=e=>z(e)===A[1],de=e=>P.includes(e)?e:P[0],V=e=>e==="flat",K=e=>q.includes(e)?e:q[0],ce="chatwoot:error",we="chatwoot:postback",ue="chatwoot:ready",ge="chatwoot:opened",he="chatwoot:closed",be=({eventName:e,data:o=null})=>{let t;return typeof window.CustomEvent=="function"?t=new CustomEvent(e,{detail:o}):(t=document.createEvent("CustomEvent"),t.initCustomEvent(e,!1,!1,o)),t},E=({eventName:e,data:o})=>{const t=be({eventName:e,data:o});window.dispatchEvent(t)},pe="M240.808 240.808H122.123C56.6994 240.808 3.45695 187.562 3.45695 122.122C3.45695 56.7031 56.6994 3.45697 122.124 3.45697C187.566 3.45697 240.808 56.7031 240.808 122.122V240.808Z",X=document.getElementsByTagName("body")[0],v=document.createElement("div"),C=document.createElement("div"),U=document.createElement("button"),$=document.createElement("button");document.createElement("span");const fe=e=>{if(j(window.$chatwoot.type)){const o=document.getElementById("woot-widget--expanded__text");o.innerText=e}},me=({className:e,path:o,target:t})=>{let c=`${e} woot-elements--${window.$chatwoot.position}`;const r=document.createElementNS("http://www.w3.org/2000/svg","svg");r.setAttributeNS(null,"id","woot-widget-bubble-icon"),r.setAttributeNS(null,"width","24"),r.setAttributeNS(null,"height","24"),r.setAttributeNS(null,"viewBox","0 0 240 240"),r.setAttributeNS(null,"fill","none"),r.setAttribute("xmlns","http://www.w3.org/2000/svg");const n=document.createElementNS("http://www.w3.org/2000/svg","path");if(n.setAttributeNS(null,"d",o),n.setAttributeNS(null,"fill","#FFFFFF"),r.appendChild(n),t.appendChild(r),j(window.$chatwoot.type)){const u=document.createElement("div");u.id="woot-widget--expanded__text",u.innerText="",t.appendChild(u),c+=" woot-widget--expanded"}return t.className=c,t.title="Open chat window",t},ve=e=>{e&&y(C,"woot-hidden"),y(C,"woot--bubble-holder"),C.id="cw-bubble-holder",C.dataset.turboPermanent=!0,X.appendChild(C)},xe=e=>{g.events.onBubbleToggle(e),e?E({eventName:ge}):(E({eventName:he}),U.focus())},S=(e={})=>{const{toggleValue:o}=e,{isOpen:t}=window.$chatwoot;if(t===o)return;const c=o===void 0?!t:o;window.$chatwoot.isOpen=c,k(U,"woot--hide"),k($,"woot--hide"),k(v,"woot--hide"),xe(c)},ye=()=>{C.addEventListener("click",S)},Ce=()=>{const e=document.querySelector(".woot-widget-holder");y(e,"has-unread-view")},Y=()=>{const e=document.querySelector(".woot-widget-holder");_(e,"has-unread-view")},Ee=e=>{const o=e.replace("#",""),t=parseInt(o.substr(0,2),16),c=parseInt(o.substr(2,2),16),r=parseInt(o.substr(4,2),16);return(t*299+c*587+r*114)/1e3>225},Se="SET_USER_ERROR";function Be(e){return e&&e.__esModule&&Object.prototype.hasOwnProperty.call(e,"default")?e.default:e}var D={exports:{}},L={exports:{}},G;function _e(){return G||(G=1,(function(){var e="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/",o={rotl:function(t,c){return t<<c|t>>>32-c},rotr:function(t,c){return t<<32-c|t>>>c},endian:function(t){if(t.constructor==Number)return o.rotl(t,8)&16711935|o.rotl(t,24)&4278255360;for(var c=0;c<t.length;c++)t[c]=o.endian(t[c]);return t},randomBytes:function(t){for(var c=[];t>0;t--)c.push(Math.floor(Math.random()*256));return c},bytesToWords:function(t){for(var c=[],r=0,n=0;r<t.length;r++,n+=8)c[n>>>5]|=t[r]<<24-n%32;return c},wordsToBytes:function(t){for(var c=[],r=0;r<t.length*32;r+=8)c.push(t[r>>>5]>>>24-r%32&255);return c},bytesToHex:function(t){for(var c=[],r=0;r<t.length;r++)c.push((t[r]>>>4).toString(16)),c.push((t[r]&15).toString(16));return c.join("")},hexToBytes:function(t){for(var c=[],r=0;r<t.length;r+=2)c.push(parseInt(t.substr(r,2),16));return c},bytesToBase64:function(t){for(var c=[],r=0;r<t.length;r+=3)for(var n=t[r]<<16|t[r+1]<<8|t[r+2],u=0;u<4;u++)r*8+u*6<=t.length*8?c.push(e.charAt(n>>>6*(3-u)&63)):c.push("=");return c.join("")},base64ToBytes:function(t){t=t.replace(/[^A-Z0-9+\/]/ig,"");for(var c=[],r=0,n=0;r<t.length;n=++r%4)n!=0&&c.push((e.indexOf(t.charAt(r-1))&Math.pow(2,-2*n+8)-1)<<n*2|e.indexOf(t.charAt(r))>>>6-n*2);return c}};L.exports=o})()),L.exports}var I,J;function Z(){if(J)return I;J=1;var e={utf8:{stringToBytes:function(o){return e.bin.stringToBytes(unescape(encodeURIComponent(o)))},bytesToString:function(o){return decodeURIComponent(escape(e.bin.bytesToString(o)))}},bin:{stringToBytes:function(o){for(var t=[],c=0;c<o.length;c++)t.push(o.charCodeAt(c)&255);return t},bytesToString:function(o){for(var t=[],c=0;c<o.length;c++)t.push(String.fromCharCode(o[c]));return t.join("")}}};return I=e,I}/*!
 * Determine if an object is a Buffer
 *
 * @author   Feross Aboukhadijeh <https://feross.org>
 * @license  MIT
 */var O,Q;function $e(){if(Q)return O;Q=1,O=function(t){return t!=null&&(e(t)||o(t)||!!t._isBuffer)};function e(t){return!!t.constructor&&typeof t.constructor.isBuffer=="function"&&t.constructor.isBuffer(t)}function o(t){return typeof t.readFloatLE=="function"&&typeof t.slice=="function"&&e(t.slice(0,0))}return O}var ee;function Te(){return ee||(ee=1,(function(){var e=_e(),o=Z().utf8,t=$e(),c=Z().bin,r=function(n,u){n.constructor==String?u&&u.encoding==="binary"?n=c.stringToBytes(n):n=o.stringToBytes(n):t(n)?n=Array.prototype.slice.call(n,0):!Array.isArray(n)&&n.constructor!==Uint8Array&&(n=n.toString());for(var i=e.bytesToWords(n),h=n.length*8,s=1732584193,a=-271733879,d=-1732584194,l=271733878,w=0;w<i.length;w++)i[w]=(i[w]<<8|i[w]>>>24)&16711935|(i[w]<<24|i[w]>>>8)&4278255360;i[h>>>5]|=128<<h%32,i[(h+64>>>9<<4)+14]=h;for(var b=r._ff,p=r._gg,f=r._hh,m=r._ii,w=0;w<i.length;w+=16){var Ve=s,Ke=a,Xe=d,Ye=l;s=b(s,a,d,l,i[w+0],7,-680876936),l=b(l,s,a,d,i[w+1],12,-389564586),d=b(d,l,s,a,i[w+2],17,606105819),a=b(a,d,l,s,i[w+3],22,-1044525330),s=b(s,a,d,l,i[w+4],7,-176418897),l=b(l,s,a,d,i[w+5],12,1200080426),d=b(d,l,s,a,i[w+6],17,-1473231341),a=b(a,d,l,s,i[w+7],22,-45705983),s=b(s,a,d,l,i[w+8],7,1770035416),l=b(l,s,a,d,i[w+9],12,-1958414417),d=b(d,l,s,a,i[w+10],17,-42063),a=b(a,d,l,s,i[w+11],22,-1990404162),s=b(s,a,d,l,i[w+12],7,1804603682),l=b(l,s,a,d,i[w+13],12,-40341101),d=b(d,l,s,a,i[w+14],17,-1502002290),a=b(a,d,l,s,i[w+15],22,1236535329),s=p(s,a,d,l,i[w+1],5,-165796510),l=p(l,s,a,d,i[w+6],9,-1069501632),d=p(d,l,s,a,i[w+11],14,643717713),a=p(a,d,l,s,i[w+0],20,-373897302),s=p(s,a,d,l,i[w+5],5,-701558691),l=p(l,s,a,d,i[w+10],9,38016083),d=p(d,l,s,a,i[w+15],14,-660478335),a=p(a,d,l,s,i[w+4],20,-405537848),s=p(s,a,d,l,i[w+9],5,568446438),l=p(l,s,a,d,i[w+14],9,-1019803690),d=p(d,l,s,a,i[w+3],14,-187363961),a=p(a,d,l,s,i[w+8],20,1163531501),s=p(s,a,d,l,i[w+13],5,-1444681467),l=p(l,s,a,d,i[w+2],9,-51403784),d=p(d,l,s,a,i[w+7],14,1735328473),a=p(a,d,l,s,i[w+12],20,-1926607734),s=f(s,a,d,l,i[w+5],4,-378558),l=f(l,s,a,d,i[w+8],11,-2022574463),d=f(d,l,s,a,i[w+11],16,1839030562),a=f(a,d,l,s,i[w+14],23,-35309556),s=f(s,a,d,l,i[w+1],4,-1530992060),l=f(l,s,a,d,i[w+4],11,1272893353),d=f(d,l,s,a,i[w+7],16,-155497632),a=f(a,d,l,s,i[w+10],23,-1094730640),s=f(s,a,d,l,i[w+13],4,681279174),l=f(l,s,a,d,i[w+0],11,-358537222),d=f(d,l,s,a,i[w+3],16,-722521979),a=f(a,d,l,s,i[w+6],23,76029189),s=f(s,a,d,l,i[w+9],4,-640364487),l=f(l,s,a,d,i[w+12],11,-421815835),d=f(d,l,s,a,i[w+15],16,530742520),a=f(a,d,l,s,i[w+2],23,-995338651),s=m(s,a,d,l,i[w+0],6,-198630844),l=m(l,s,a,d,i[w+7],10,1126891415),d=m(d,l,s,a,i[w+14],15,-1416354905),a=m(a,d,l,s,i[w+5],21,-57434055),s=m(s,a,d,l,i[w+12],6,1700485571),l=m(l,s,a,d,i[w+3],10,-1894986606),d=m(d,l,s,a,i[w+10],15,-1051523),a=m(a,d,l,s,i[w+1],21,-2054922799),s=m(s,a,d,l,i[w+8],6,1873313359),l=m(l,s,a,d,i[w+15],10,-30611744),d=m(d,l,s,a,i[w+6],15,-1560198380),a=m(a,d,l,s,i[w+13],21,1309151649),s=m(s,a,d,l,i[w+4],6,-145523070),l=m(l,s,a,d,i[w+11],10,-1120210379),d=m(d,l,s,a,i[w+2],15,718787259),a=m(a,d,l,s,i[w+9],21,-343485551),s=s+Ve>>>0,a=a+Ke>>>0,d=d+Xe>>>0,l=l+Ye>>>0}return e.endian([s,a,d,l])};r._ff=function(n,u,i,h,s,a,d){var l=n+(u&i|~u&h)+(s>>>0)+d;return(l<<a|l>>>32-a)+u},r._gg=function(n,u,i,h,s,a,d){var l=n+(u&h|i&~h)+(s>>>0)+d;return(l<<a|l>>>32-a)+u},r._hh=function(n,u,i,h,s,a,d){var l=n+(u^i^h)+(s>>>0)+d;return(l<<a|l>>>32-a)+u},r._ii=function(n,u,i,h,s,a,d){var l=n+(i^(u|~h))+(s>>>0)+d;return(l<<a|l>>>32-a)+u},r._blocksize=16,r._digestsize=16,D.exports=function(n,u){if(n==null)throw new Error("Illegal argument "+n);var i=e.wordsToBytes(r(n,u));return u&&u.asBytes?i:u&&u.asString?c.bytesToString(i):e.bytesToHex(i)}})()),D.exports}var Me=Te();const Fe=Be(Me),te=["avatar_url","email","name"],ke=[...te,"identifier_hash"],R=()=>{const e="cw_user_",{websiteToken:o}=window.$chatwoot;return`${e}${o}`},Ae=({identifier:e="",user:o})=>`${ke.reduce((c,r)=>`${c}${r}${o[r]||""}`,"")}identifier${e}`,Ue=(...e)=>Fe(Ae(...e)),De=e=>te.reduce((o,t)=>o||!!e[t],!1),N=(e,o,{expires:t=365,baseDomain:c=void 0}={})=>{const r={expires:t,sameSite:"Lax",domain:c};typeof o=="object"&&(o=JSON.stringify(o)),x.set(e,o,r)},oe=["click","touchstart","keypress","keydown"],Le=()=>{let e;try{e=new(window.AudioContext||window.webkitAudioContext)}catch{}return e},Ie=async(e="",o)=>{const t=Le(),c=r=>{window.playAudioAlert=()=>{if(t){const n=t.createBufferSource();n.buffer=r,n.connect(t.destination),n.loop=!1,n.start()}}};if(t){const{type:r="dashboard",alertTone:n="ding"}=o||{},u=`${e}/audio/${r}/${n}.mp3`,i=new Request(u);fetch(i).then(h=>h.arrayBuffer()).then(h=>(t.decodeAudioData(h).then(c),new Promise(s=>s()))).catch(()=>{})}},Oe=({origin:e,conversationCookie:o,websiteToken:t,locale:c})=>{const r=new URL("/widget",e);return r.searchParams.append("cw_conversation",o),r.searchParams.append("website_token",t),r.searchParams.append("locale",c),r.toString()},Re=(e,o,t,c)=>{try{const r=Oe({origin:e,websiteToken:o,locale:t,conversationCookie:c});window.open(r,`webwidget_session_${o}`,"resizable=off,width=400,height=600").focus()}catch(r){console.log(r)}};function ne(e){if(e===null||e===!0||e===!1)return NaN;var o=Number(e);return isNaN(o)?o:o<0?Math.ceil(o):Math.floor(o)}function H(e,o){if(o.length<e)throw new TypeError(e+" argument"+(e>1?"s":"")+" required, but only "+o.length+" present")}function Ne(e){H(1,arguments);var o=Object.prototype.toString.call(e);return e instanceof Date||typeof e=="object"&&o==="[object Date]"?new Date(e.getTime()):typeof e=="number"||o==="[object Number]"?new Date(e):((typeof e=="string"||o==="[object String]")&&typeof console<"u"&&(console.warn("Starting with v2.0.0-beta.1 date-fns doesn't accept strings as date arguments. Please use `parseISO` to parse strings. See: https://git.io/fjule"),console.warn(new Error().stack)),new Date(NaN))}function He(e,o){H(2,arguments);var t=Ne(e).getTime(),c=ne(o);return new Date(t+c)}var We=36e5;function Pe(e,o){H(2,arguments);var t=ne(o);return He(e,t*We)}const ie=(e,o="")=>N("cw_conversation",e,{baseDomain:o}),qe=e=>{const o=Pe(new Date,1);N("cw_snooze_campaigns_till",Number(o),{expires:o,baseDomain:e})},g={getUrl({baseUrl:e,websiteToken:o}){return`${e}/widget?website_token=${o}`},createFrame:({baseUrl:e,websiteToken:o})=>{if(g.getAppFrame())return;se();const t=document.createElement("iframe"),c=x.get("cw_conversation");let r=g.getUrl({baseUrl:e,websiteToken:o});c&&(r=`${r}&cw_conversation=${c}`),t.src=r,t.allow="camera;microphone;fullscreen;display-capture;picture-in-picture;clipboard-write;",t.id="chatwoot_live_chat_widget",t.style.visibility="hidden";let n=`woot-widget-holder woot--hide woot-elements--${window.$chatwoot.position}`;window.$chatwoot.hideMessageBubble&&(n+=" woot-widget--without-bubble"),V(window.$chatwoot.widgetStyle)&&(n+=" woot-widget-holder--flat"),y(v,n),v.id="cw-widget-holder",v.dataset.turboPermanent=!0,v.appendChild(t),X.appendChild(v),g.initPostMessageCommunication(),g.initWindowSizeListener(),g.preventDefaultScroll()},getAppFrame:()=>document.getElementById("chatwoot_live_chat_widget"),getBubbleHolder:()=>document.getElementsByClassName("woot--bubble-holder"),sendMessage:(e,o)=>{g.getAppFrame().contentWindow.postMessage(`chatwoot-widget:${JSON.stringify({event:e,...o})}`,"*")},initPostMessageCommunication:()=>{window.onmessage=e=>{if(typeof e.data!="string"||e.data.indexOf("chatwoot-widget:")!==0)return;const o=JSON.parse(e.data.replace("chatwoot-widget:",""));typeof g.events[o.event]=="function"&&g.events[o.event](o)}},initWindowSizeListener:()=>{window.addEventListener("resize",()=>g.toggleCloseButton())},preventDefaultScroll:()=>{v.addEventListener("wheel",e=>{const o=e.deltaY,t=v.scrollHeight,c=v.offsetHeight,r=v.scrollTop;(r===0&&o<0||c+r===t&&o>0)&&e.preventDefault()})},setFrameHeightToFitContent:(e,o)=>{const t=g.getAppFrame(),c=o?`${e}px`:"100%";t&&t.setAttribute("style",`height: ${c} !important`)},setupAudioListeners:()=>{const{baseUrl:e=""}=window.$chatwoot;Ie(e,{type:"widget",alertTone:"ding"}).then(()=>oe.forEach(o=>{document.removeEventListener(o,g.setupAudioListeners,!1)}))},events:{loaded:e=>{ie(e.config.authToken,window.$chatwoot.baseDomain),window.$chatwoot.hasLoaded=!0;const o=x.get("cw_snooze_campaigns_till");g.sendMessage("config-set",{locale:window.$chatwoot.locale,position:window.$chatwoot.position,hideMessageBubble:window.$chatwoot.hideMessageBubble,showPopoutButton:window.$chatwoot.showPopoutButton,widgetStyle:window.$chatwoot.widgetStyle,darkMode:window.$chatwoot.darkMode,showUnreadMessagesDialog:window.$chatwoot.showUnreadMessagesDialog,campaignsSnoozedTill:o,welcomeTitle:window.$chatwoot.welcomeTitle,welcomeDescription:window.$chatwoot.welcomeDescription,availableMessage:window.$chatwoot.availableMessage,unavailableMessage:window.$chatwoot.unavailableMessage,enableFileUpload:window.$chatwoot.enableFileUpload,enableEmojiPicker:window.$chatwoot.enableEmojiPicker,enableEndConversation:window.$chatwoot.enableEndConversation}),g.onLoad({widgetColor:e.config.channelConfig.widgetColor}),g.toggleCloseButton(),window.$chatwoot.user&&g.sendMessage("set-user",window.$chatwoot.user),window.playAudioAlert=()=>{},oe.forEach(t=>{document.addEventListener(t,g.setupAudioListeners,!1)}),window.$chatwoot.resetTriggered||E({eventName:ue})},error:({errorType:e,data:o})=>{E({eventName:ce,data:o}),e===Se&&x.remove(R())},onEvent({eventIdentifier:e,data:o}){E({eventName:e,data:o})},setBubbleLabel(e){fe(window.$chatwoot.launcherTitle||e.label)},setAuthCookie({data:{widgetAuthToken:e}}){ie(e,window.$chatwoot.baseDomain)},setCampaignReadOn(){qe(window.$chatwoot.baseDomain)},postback(e){E({eventName:we,data:e})},toggleBubble:e=>{let o={};e==="open"?o.toggleValue=!0:e==="close"&&(o.toggleValue=!1),S(o)},popoutChatWindow:({baseUrl:e,websiteToken:o,locale:t})=>{const c=x.get("cw_conversation");window.$chatwoot.toggle("close"),Re(e,o,t,c)},closeWindow:()=>{S({toggleValue:!1}),Y()},onBubbleToggle:e=>{g.sendMessage("toggle-open",{isOpen:e}),e&&g.pushEvent("webwidget.triggered")},onLocationChange:({referrerURL:e,referrerHost:o})=>{g.sendMessage("change-url",{referrerURL:e,referrerHost:o})},updateIframeHeight:e=>{const{extraHeight:o=0,isFixedHeight:t}=e;g.setFrameHeightToFitContent(o,t)},setUnreadMode:()=>{Ce(),S({toggleValue:!0})},resetUnreadMode:()=>Y(),handleNotificationDot:e=>{if(window.$chatwoot.hideMessageBubble)return;const o=document.querySelector(".woot-widget-bubble");e.unreadMessageCount>0&&!o.classList.contains("unread-notification")?y(o,"unread-notification"):e.unreadMessageCount===0&&_(o,"unread-notification")},closeChat:()=>{S({toggleValue:!1})},playAudio:()=>{window.playAudioAlert()}},pushEvent:e=>{g.sendMessage("push-event",{eventName:e})},onLoad:({widgetColor:e})=>{const o=g.getAppFrame();if(o.style.visibility="",o.setAttribute("id","chatwoot_live_chat_widget"),g.getBubbleHolder().length)return;ve(window.$chatwoot.hideMessageBubble),le();let t="woot-widget-bubble",c=`woot-elements--${window.$chatwoot.position} woot-widget-bubble woot--close woot--hide`;V(window.$chatwoot.widgetStyle)&&(t+=" woot-widget-bubble--flat",c+=" woot-widget-bubble--flat"),Ee(e)&&(t+=" woot-widget-bubble-color--lighter",c+=" woot-widget-bubble-color--lighter");const r=me({className:t,path:pe,target:U});y($,c),r.style.background=e,$.style.background=e,C.appendChild(r),C.appendChild($),ye()},toggleCloseButton:()=>{let e=!1;window.matchMedia("(max-width: 668px)").matches&&(e=!0),g.sendMessage("toggle-close-button",{isMobile:e})}},ze="sdk-set-bubble-visibility",je=({baseUrl:e,websiteToken:o})=>{if(window.$chatwoot)return;document.addEventListener("turbo:before-render",n=>{n.detail.renderMethod!=="morph"&&F(n.detail.newBody)}),window.Turbolinks&&document.addEventListener("turbolinks:before-render",n=>{F(n.data.newBody)}),document.addEventListener("astro:before-swap",n=>F(n.newDocument.body));const t=window.chatwootSettings||{};let c=t.locale,r=t.baseDomain;t.useBrowserLanguage&&(c=window.navigator.language.replace("-","_")),window.$chatwoot={baseUrl:e,baseDomain:r,hasLoaded:!1,hideMessageBubble:t.hideMessageBubble||!1,isOpen:!1,position:t.position==="left"?"left":"right",websiteToken:o,locale:c,useBrowserLanguage:t.useBrowserLanguage||!1,type:z(t.type),launcherTitle:t.launcherTitle||"",showPopoutButton:t.showPopoutButton||!1,showUnreadMessagesDialog:t.showUnreadMessagesDialog??!0,widgetStyle:de(t.widgetStyle)||"standard",resetTriggered:!1,darkMode:K(t.darkMode),welcomeTitle:t.welcomeTitle||"",welcomeDescription:t.welcomeDescription||"",availableMessage:t.availableMessage||"",unavailableMessage:t.unavailableMessage||"",enableFileUpload:t.enableFileUpload,enableEmojiPicker:t.enableEmojiPicker??!0,enableEndConversation:t.enableEndConversation??!0,toggle(n){g.events.toggleBubble(n)},toggleBubbleVisibility(n){let u=document.querySelector(".woot--bubble-holder"),i=document.querySelector(".woot-widget-holder");n==="hide"?(y(i,"woot-widget--without-bubble"),y(u,"woot-hidden"),window.$chatwoot.hideMessageBubble=!0):n==="show"&&(_(u,"woot-hidden"),_(i,"woot-widget--without-bubble"),window.$chatwoot.hideMessageBubble=!1),g.sendMessage(ze,{hideMessageBubble:window.$chatwoot.hideMessageBubble})},popoutChatWindow(){g.events.popoutChatWindow({baseUrl:window.$chatwoot.baseUrl,websiteToken:window.$chatwoot.websiteToken,locale:c})},setUser(n,u){if(typeof n!="string"&&typeof n!="number")throw new Error("Identifier should be a string or a number");if(!De(u))throw new Error("User object should have one of the keys [avatar_url, email, name]");const i=R(),h=x.get(i),s=Ue({identifier:n,user:u});s!==h&&(window.$chatwoot.identifier=n,window.$chatwoot.user=u,g.sendMessage("set-user",{identifier:n,user:u}),N(i,s,{baseDomain:r}))},setCustomAttributes(n={}){if(!n||!Object.keys(n).length)throw new Error("Custom attributes should have atleast one key");g.sendMessage("set-custom-attributes",{customAttributes:n})},deleteCustomAttribute(n=""){if(n)g.sendMessage("delete-custom-attribute",{customAttribute:n});else throw new Error("Custom attribute is required")},setConversationCustomAttributes(n={}){if(!n||!Object.keys(n).length)throw new Error("Custom attributes should have atleast one key");g.sendMessage("set-conversation-custom-attributes",{customAttributes:n})},deleteConversationCustomAttribute(n=""){if(n)g.sendMessage("delete-conversation-custom-attribute",{customAttribute:n});else throw new Error("Custom attribute is required")},setLabel(n=""){g.sendMessage("set-label",{label:n})},removeLabel(n=""){g.sendMessage("remove-label",{label:n})},setLocale(n="en"){g.sendMessage("set-locale",{locale:n})},setColorScheme(n="light"){g.sendMessage("set-color-scheme",{darkMode:K(n)})},reset(){window.$chatwoot.isOpen&&g.events.toggleBubble(),x.remove("cw_conversation"),x.remove(R());const n=g.getAppFrame();n.src=g.getUrl({baseUrl:window.$chatwoot.baseUrl,websiteToken:window.$chatwoot.websiteToken}),window.$chatwoot.resetTriggered=!0}},g.createFrame({baseUrl:e,websiteToken:o})};window.chatwootSDK={run:je}})();
