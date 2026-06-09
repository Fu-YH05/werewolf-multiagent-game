import GameScene from './GameScene';
import GameLog from './GameLog';

export default function MainContent() {
  return (
    <div className="flex h-[calc(100vh-64px)]">
      <GameScene />
      <GameLog />
    </div>
  );
}
