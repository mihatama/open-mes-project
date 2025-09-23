import React, { useState } from 'react';
import './Help.css';
import InventoryInquiryLayoutDiagram from '../components/InventoryInquiryLayoutDiagram';
import ModelDisplaySettingsLayoutDiagram from '../components/ModelDisplaySettingsLayoutDiagram';
import FeatureOverviewDiagram from '../components/FeatureOverviewDiagram';

// Helper function to create topic content
const createTopic = (id, title, Component) => ({ id, title, Component });

const helpTopics = [
  createTopic('inventory-inquiry-usage', '在庫照会画面の使い方', () => (
    <>
      <h3>在庫照会画面の使い方</h3>
      <p>在庫照会画面では、現在の在庫状況を確認したり、数量や場所を修正したりすることができます。</p>
      <InventoryInquiryLayoutDiagram />

      <h4>① 検索エリア</h4>
      <p>画面の上部にある検索エリアで、表示したい在庫を絞り込むことができます。</p>
      <ul>
        <li><strong>検索フィールド:</strong> 「品番」や「倉庫」などの入力欄にキーワードを入れて検索します。</li>
        <li><strong>在庫有チェックボックス:</strong> チェックを入れると、在庫が1つ以上ある品目のみに絞り込めます。</li>
        <li><strong>検索ボタン:</strong> クリックすると、指定した条件で在庫一覧を再表示します。</li>
      </ul>

      <h4>② 在庫一覧エリア</h4>
      <p>検索条件に一致した在庫が一覧で表示されます。各行の右端には操作ボタンがあります。</p>
      <ul>
        <li><strong>移動ボタン:</strong> 在庫を別の倉庫や場所へ移動させるための画面を開きます。</li>
        <li><strong>修正ボタン:</strong> 在庫の数量や場所を修正するための画面を開きます。</li>
      </ul>

      <h4>③ ページネーションエリア</h4>
      <p>検索結果が複数ページにわたる場合、このエリアでページを移動できます。</p>
      <ul>
        <li><strong>前へ/次へボタン:</strong> 表示するページを切り替えます。</li>
        <li><strong>ページ情報:</strong> 現在のページ番号、総ページ数、全件数が表示されます。</li>
      </ul>
    </>
  )),
  createTopic('model-display-settings-usage', 'ページ項目表示設定（管理者）', () => (
    <>
      <h3>ページ項目表示設定（管理者）</h3>
      <p>管理者ユーザーは、この画面で各一覧ページの表示項目をカスタマイズできます。</p>
      <ModelDisplaySettingsLayoutDiagram />

      <h4>① データ種別選択</h4>
      <p>まず、設定を変更したい画面（データ種別）をドロップダウンから選択します。例えば「在庫照会」ページであれば、それに対応するデータ種別を選択してください。</p>

      <h4>② 設定テーブル</h4>
      <p>選択したデータ種別の項目が一覧で表示されます。ここで各項目の表示方法をカスタマイズします。</p>
      <ul>
        <li><strong>順序の変更:</strong> 行の左端にある「↕」マークを掴んで上下にドラッグ＆ドロップすると、一覧画面での表示順序を入れ替えられます。</li>
        <li><strong>カスタム表示名:</strong> 項目の表示名を変更したい場合に入力します。空欄のままだと、システムのデフォルト名が使われます。</li>
        <li><strong>一覧表示:</strong> このスイッチをONにすると、その項目が一覧画面のテーブルに表示されるようになります。</li>
        <li><strong>検索対象:</strong> このスイッチをONにすると、画面上部のキーワード検索の対象にこの項目が含まれるようになります。</li>
      </ul>

      <h4>③ 保存ボタン</h4>
      <p>すべての設定が終わったら、最後に画面上部にある「この設定で保存」ボタンを押して変更を適用します。</p>
    </>
  )),
  createTopic('system-design', 'システム設計', () => (
    <>
      <h3>ページ項目表示設定の仕組み</h3>
      <p>各ページのテーブルに表示される項目や、検索に使用できる項目は、管理者が設定した内容に基づいて動的に変更されます。</p>
      <p>下の図は、管理者が表示項目を設定し、それがユーザーの画面に反映されるまでの流れを示しています。</p>
      <FeatureOverviewDiagram />
      <p>もし表示したい項目が表示されていない場合や、特定の条件で検索したいのに検索項目がない場合は、システム管理者に連絡してください。</p>
    </>
  )),
];

const Help = () => {
  const [activeTopic, setActiveTopic] = useState(helpTopics[0].id);

  const renderContent = () => {
    const topic = helpTopics.find(t => t.id === activeTopic);
    if (!topic) {
      return <p>トピックを選択してください。</p>;
    }
    const { Component } = topic;
    return (
      <div>
        <h2>{topic.title}</h2>
        <Component />
      </div>
    );
  };

  return (
    <div className="help-container">
      <div className="help-sidebar">
        <h3>ヘルプ トピック</h3>
        <ul>
          {helpTopics.map(topic => (
            <li
              key={topic.id}
              className={activeTopic === topic.id ? 'active' : ''}
              onClick={() => setActiveTopic(topic.id)}
            >
              {topic.title}
            </li>
          ))}
        </ul>
      </div>
      <div className="help-content">
        {renderContent()}
      </div>
    </div>
  );
};

export default Help;