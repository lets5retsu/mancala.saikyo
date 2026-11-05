async function trainSelfPlay(total){
 if(training||watching||busy)return;
 training=true;$("trainButton").disabled=true;$("watchCpu").disabled=true;$("newGame").disabled=true;
 $("trainingProgress").textContent="学習準備中…";
 
 let w=0, l=0, d=0, completed=0;
 let intervalW=0, intervalL=0, intervalD=0; // 500局区間用の集計カウンタ
 let csvLog = "累計対局数,区間先手勝率(%),区間後手勝率(%),区間引き分け率(%),累計先手勝率(%),累計後手勝率(%)\n";

 for(let g=0; g<total; g++){
  let s=initialState(), plies=0;
  while(!terminal(s) && plies<250){
   const before=s, move=trainingMove(s, Math.max(0.035, 0.22*(1-g/total)));
   if(move===null) break;
   s=applyUnchecked(s, move); tdUpdate(before, s); plies++;
  }
  
  // 勝敗カウント
  const isWin = s.scores[0] > s.scores[1];
  const isLoss = s.scores[0] < s.scores[1];
  const isDraw = s.scores[0] === s.scores[1];

  if(isWin) { w++; intervalW++; }
  else if(isLoss) { l++; intervalL++; }
  else { d++; intervalD++; }

  learning.games++;
  learning.wins += isWin ? 1 : 0;
  learning.losses += isLoss ? 1 : 0;
  learning.draws += isDraw ? 1 : 0;
  completed++;

  // 500局ごと（および最終局）にデータを記録
  if(completed % 500 === 0 || completed === total){
   const intervalTotal = intervalW + intervalL + intervalD;
   const p0IntervalWinRate = ((intervalW / intervalTotal) * 100).toFixed(1);
   const p1IntervalWinRate = ((intervalL / intervalTotal) * 100).toFixed(1);
   const intervalDrawRate   = ((intervalD / intervalTotal) * 100).toFixed(1);
   
   const p0CumWinRate = ((w / completed) * 100).toFixed(1);
   const p1CumWinRate = ((l / completed) * 100).toFixed(1);

   // CSV行の追加
   csvLog += `${completed},${p0IntervalWinRate},${p1IntervalWinRate},${intervalDrawRate},${p0CumWinRate},${p1CumWinRate}\n`;

   // 区間カウンタのリセット
   intervalW = 0; intervalL = 0; intervalD = 0;
  }

  if(completed % 10 === 0 || completed === total){
   $("trainingProgress").textContent = `学習中：${completed.toLocaleString()} / ${total.toLocaleString()}局（今回 先手勝 ${w}・後手勝 ${l}・引分 ${d}）`;
   updateLearningStatus();
   await new Promise(r => setTimeout(r, 0));
  }
 }

 saveLearning();
 
 // ブラウザのデベロッパーツール（Console）にExcel貼付用CSVを出力
 console.log("--- 500局ごとの学習結果ログ (CSV) ---");
 console.log(csvLog);

 $("trainingProgress").textContent = `学習完了：${completed.toLocaleString()}局を追加しました。コンソール(F12)に500局ごとの詳細データを出力しました。`;
 training=false; $("trainButton").disabled=false; $("watchCpu").disabled=false; $("newGame").disabled=false;
}
