_base_ = [
    '../_base_/dataset_v1.py',
    '../_base_/optimizer.py',
    '../_base_/schedule.py',
]

img_size = [768, 1600]
num_rays = [48, 100]
amp = False
max_epochs = 12
warmup_iters = 1000
sem = True

multisteplr = True
multisteplr_config = dict(
    decay_t = [3516 * 9],
    decay_rate = 0.1,
    warmup_t = warmup_iters,
    warmup_lr_init = 1e-6,
    t_in_epochs = False
)

optimizer = dict(
    optimizer=dict(
        type='AdamW',
        lr=1e-4,
        weight_decay=0.01,
        # eps=1e-4
    ),
    paramwise_cfg=dict(
        custom_keys={
            'img_backbone': dict(lr_mult=0.1),}
    ),
)


data_path = 'data/nuscenes/'

train_dataset_config = dict(
    _delete_=True,
    type='nuScenes_One_Frame_Sweeps_Dist',
    data_path = data_path,
    imageset = 'data/nuscenes_infos_train_sweeps.pkl',
    crop_size = img_size,
    min_dist = 0.4,
    max_dist = 30.0,
    strict = True,
    return_depth = False,
    eval_depth = 80,
    cur_prob = 0.333,
    prev_prob = 0.5,
    choose_nearest = True,
    ref_sensor = 'CAM_FRONT',
    composite_prev_next=True,
    sensor_mus=[0.5, 0.5],
    sensor_sigma=0.5,
    ego_centric=True,
)
    
val_dataset_config = dict(
    _delete_=True,
    type='nuScenes_One_Frame_Sweeps_Dist',
    data_path = data_path,
    imageset = 'data/nuscenes_infos_val_sweeps.pkl',
    crop_size = img_size,
    min_dist = 0.4,
    max_dist = 30.0,
    strict = False,
    return_depth = True,
    eval_depth = 80,
    cur_prob = 1,
    prev_prob = 0.5,
    choose_nearest = True,
    ref_sensor = 'CAM_FRONT',
    composite_prev_next=True,
    sensor_mus=[0.5, 0.5],
    sensor_sigma=0.5,
    ego_centric=True
)

train_wrapper_config = dict(
    type='tpvformer_dataset_nuscenes_temporal',
    phase='train', 
    scale_rate=0.5,
    photometric_aug=dict(
        use_swap_channel=False,
    )
)

val_wrapper_config = dict(
    type='tpvformer_dataset_nuscenes_temporal',
    phase='val', 
    scale_rate=0.5,
    photometric_aug=dict(
        use_swap_channel=False,
    )
)

train_loader = dict(
    batch_size = 1,
    shuffle = True,
    num_workers = 1,
)
    
val_loader = dict(
    batch_size = 1,
    shuffle = False,
    num_workers = 1,
)

loss = dict(
    type='MultiLoss',
    loss_cfgs=[
        dict(
            type='ReprojLossMonoMultiNewCombine',
            weight=1.0,
            no_ssim=False,
            img_size=img_size,
            ray_resize=num_rays,
            input_dict={
                'curr_imgs': 'curr_imgs',
                'prev_imgs': 'prev_imgs',
                'next_imgs': 'next_imgs',
                'ray_indices': 'ray_indices',
                'weights': 'weights',
                'ts': 'ts',
                'metas': 'metas',
                'ms_rays': 'ms_rays',
                # 'deltas': 'deltas'
                }),
        dict(
            type='RGBLossMS',
            weight=0.1,
            img_size=img_size,
            no_ssim=False,
            ray_resize=num_rays,
            input_dict={
                'ms_colors': 'ms_colors',
                'ms_rays': 'ms_rays',
                'gt_imgs': 'color_imgs'}),
        dict(
            type='EikonalLoss',
            weight=0.1,),
        dict(
            type='SecondGradLoss',
            weight=0.01),
        dict(
            type='SemLossMS',
            weight=0.1,
            img_size=img_size,
            ray_resize=num_rays,
            input_dict={
                'sem': 'sem',
                'metas': 'metas',
                'ms_rays': 'ms_rays'}),
        dict(
            type='SoftSparsityLoss',
            weight=0.001,
            input_dict={
                'density': 'uniform_sdf'})
        # dict(
        #     type='SparsityLoss',
        #     weight=0.001,
        #     scale=0.1,
        #     input_dict={
        #         'density': 'uniform_sdf'}),
        ])

loss_input_convertion = dict(
    ms_depths='ms_depths',
    ms_rays='ms_rays',
    # ms_accs='ms_accs',
    ms_colors='ms_colors',
    ray_indices='ray_indices',
    weights='weights',
    ts='ts',
    eik_grad='eik_grad',
    second_grad='second_grad',
    sem='sem',
    # sdfs='sample_sdf'
    uniform_sdf='uniform_sdf',
    # deltas='deltas'
)

load_from = ''

_dim_ = 96
_ffn_dim_ = 2 * _dim_
num_heads = 6
mapping_args = dict(
    nonlinear_mode='linear',
    h_size=[128, 0],
    h_range=[40.0, 0],
    h_half=False,
    w_size=[128, 0],
    w_range=[40.0, 0],
    w_half=False,
    d_size=[24, 0],
    d_range=[-1.0, 5.4, 5.4]
)
# bev_inner = 160
# bev_outer = 1
# range_inner = 80.0
# range_outer = 1.0
# nonlinear_mode = 'linear_upscale'
# z_inner = 20
# z_outer = 10
# z_ranges = [-4.0, 4.0, 12.0]
tpv_h = 1 + 2 * 128
tpv_w = 1 + 2 * 128
tpv_z = 1 + 24
point_cloud_range = [-40.0, -40.0, -1.0, 40.0, 40.0, 5.4]

num_points_cross = 8
num_points_self = 12


self_cross_layer = dict(
    type='BEVFormerLayer',
    attn_cfgs=[
        dict(
            type='MultiScaleDeformableAttention',
            embed_dims=_dim_,
            num_heads=num_heads,
            num_levels=1,
            num_points=num_points_self,
            dropout=0.1,
            batch_first=True),
        dict(
            type='BEVCrossAttention',
            embed_dims=_dim_,
            num_cams=6,
            dropout=0.1,
            batch_first=True,
            deformable_attention=dict(
                type='BEVDeformableAttention',
                embed_dims=_dim_,
                num_heads=num_heads,
                num_levels=4,
                num_points=num_points_cross,
                dropout=0.1,
                batch_first=True))
    ],
    feedforward_channels=_ffn_dim_,
    ffn_dropout=0.1,
    operation_order=('self_attn', 'norm', 'cross_attn', 'norm', 'ffn', 'norm')
)


model = dict(
    type='TPVSegmentor',
    img_backbone_out_indices=[0, 1, 2, 3],
    img_backbone=dict(
        type='ResNet',
        depth=50,
        num_stages=4,
        out_indices=(0, 1, 2, 3),
        frozen_stages=0,
        norm_eval=False,
        style='pytorch',
        pretrained='./ckpts/resnet50-0676ba61.pth'),
    img_neck=dict(
        type='FPN',
        in_channels=[256, 512, 1024, 2048],
        out_channels=_dim_,
        start_level=0,
        add_extra_convs='on_output',
        num_outs=4,
        relu_before_extra_convs=True),
    lifter=dict(
        type='BEVQueryLifter',
        bev_h=tpv_h,
        bev_w=tpv_w, 
        dim=_dim_),
    encoder=dict(
        type='BEVFormerEncoder',
        # bev_inner=bev_inner,
        # bev_outer=bev_outer,
        # range_inner=range_inner,
        # range_outer=range_outer,
        # nonlinear_mode=nonlinear_mode,
        # z_inner=z_inner,
        # z_outer=z_outer,
        # z_ranges=z_ranges,
        mapping_args=mapping_args,
        # camera_aware=True,
        # camera_aware_mid_channels=96,

        embed_dims=_dim_,
        num_cams=6,
        num_feature_levels=4,
        positional_encoding=dict(
            type='BEVPositionalEncoding',
            num_freqs=12, 
            embed_dims=_dim_, 
            tot_range=point_cloud_range),
        num_points_cross=num_points_cross,
        num_points_self=num_points_self,
        transformerlayers=[
            self_cross_layer,
            self_cross_layer,
            self_cross_layer,
            self_cross_layer], 
        num_layers=4),
    head=dict(
        type='NeuSHead',
        roi_aabb=point_cloud_range, 
        resolution=0.4,
        near_plane=0.0,
        far_plane=1e10,
        num_samples=256,
        num_samples_importance=0,
        num_up_sample_steps=0,
        base_variance=4,

        beta_init=0.1,
        beta_max=0.195,
        total_iters=3516*11,
        beta_hand_tune=False,
        
        use_numerical_gradients=False,
        sample_gradient=True,
        return_uniform_sdf=True,
        return_second_grad=True,
        return_sem=True,
        return_sample_sdf=False,

        # rays args
        ray_sample_mode='cellular',    # fixed, cellular
        ray_number=num_rays,      # 192 * 400
        ray_img_size=img_size,
        ray_upper_crop=0,
        # img2lidar args
        trans_kw='temImg2lidar',
        novel_view=None,

        # render args
        render_bkgd='random',

        # bev nerf
        # bev_inner=bev_inner,
        # bev_outer=bev_outer,
        # range_inner=range_inner,
        # range_outer=range_outer,
        # nonlinear_mode=nonlinear_mode,
        # z_inner=z_inner,
        # z_outer=z_outer,
        # z_ranges=z_ranges,
        mapping_args=mapping_args,

        # mlp decoder 
        embed_dims=_dim_,
        color_dims=24,
        density_layers=2,
        sh_deg=0,
        sh_act='relu',
        two_split=False,
        tpv=False))